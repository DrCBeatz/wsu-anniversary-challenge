from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import boto3
from botocore.exceptions import ClientError

app = FastAPI()

# Add the CORS middleware
origins = [
    "https://www.wsuchallenge.ca",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a DynamoDB resource and reference the table
dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
table = dynamodb.Table("StickyNotes")

@app.get("/notes")
def list_notes():
    try:
        # 'scan' returns all items in the table
        response = table.scan()
        items = response.get("Items", [])
        return {"notes": items}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notes/{note_id}")
def claim_note(note_id: int):
    """
    Mark the note as claimed by setting isClaimed = true.
    If the note doesn't exist, or is already claimed, handle accordingly.
    """
    try:
        # Optionally, you can add a condition to prevent re-claiming
        response = table.update_item(
            Key={"noteNumber": note_id},
            UpdateExpression="SET isClaimed = :val",
            ConditionExpression="attribute_not_exists(isClaimed) OR isClaimed = :false", 
            ExpressionAttributeValues={
            ":val": True,
            ":false": False
            },
            ReturnValues="ALL_NEW"
        )

        updated_item = response.get("Attributes", {})
        
        # If 'Attributes' is empty, that might mean the note didn't exist
        if not updated_item:
            raise HTTPException(
                status_code=404,
                detail=f"Note {note_id} not found in StickyNotes table."
            )

        return {"status": "claimed", "note": updated_item}

    except ClientError as e:
        # You can parse e.response['Error']['Code'] for more specifics
        raise HTTPException(status_code=400, detail=str(e))

# Wrap the FastAPI app in Mangum for Lambda
handler = Mangum(app)

# app.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import boto3
from botocore.exceptions import ClientError

app = FastAPI()

# 1) Detect if we’re running locally or in production
LOCAL_DYNAMODB_ENDPOINT = os.getenv("LOCAL_DYNAMODB_ENDPOINT")
DYNAMODB_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-2")
TABLE_NAME = os.getenv("DYNAMODB_TABLE", "StickyNotes")

# 2) Set up CORS
# Add localhost:... to the list of allowed origins for development
origins = [
    "https://www.wsuchallenge.ca",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3) Create a DynamoDB resource pointed either at local or production
if LOCAL_DYNAMODB_ENDPOINT:
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=DYNAMODB_REGION,
        endpoint_url=LOCAL_DYNAMODB_ENDPOINT,
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy"
    )
else:
    # Production path (AWS environment)
    dynamodb = boto3.resource("dynamodb", region_name=DYNAMODB_REGION)

table = dynamodb.Table(TABLE_NAME)

@app.get("/notes")
def list_notes():
    try:
        response = table.scan()
        items = response.get("Items", [])
        return {"notes": items}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notes/{note_id}")
def claim_note(note_id: int):
    """
    Mark the note as claimed by setting isClaimed = true.
    """
    try:
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
        if not updated_item:
            raise HTTPException(
                status_code=404,
                detail=f"Note {note_id} not found."
            )

        return {"status": "claimed", "note": updated_item}

    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))

handler = Mangum(app)

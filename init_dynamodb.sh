# init_dynamodb.sh

aws dynamodb create-table \
    --table-name StickyNotes \
    --attribute-definitions AttributeName=noteNumber,AttributeType=N \
    --key-schema AttributeName=noteNumber,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-2 \
    --endpoint-url http://localhost:8000

aws dynamodb put-item \
  --table-name StickyNotes \
  --item '{"noteNumber": {"N": "5"}, "isClaimed": {"BOOL": false}}' \
  --endpoint-url http://localhost:8000 \
  --region us-east-2

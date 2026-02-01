import boto3
from typing import List
from app.application.ports.queue import QueuePort, QueueMessage


class SqsQueueAdapter(QueuePort):
    def __init__(self, region: str, queue_url: str):
        self._client = boto3.client("sqs", region_name=region)
        self._queue_url = queue_url

    def receive(self, max_messages: int, wait_time_seconds: int, visibility_timeout: int) -> List[QueueMessage]:
        resp = self._client.receive_message(
            QueueUrl=self._queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time_seconds,
            VisibilityTimeout=visibility_timeout,
            MessageAttributeNames=["All"],
            AttributeNames=["All"],
        )
        msgs = resp.get("Messages", [])
        out: List[QueueMessage] = []
        for m in msgs:
            out.append(
                QueueMessage(
                    message_id=m["MessageId"],
                    receipt_handle=m["ReceiptHandle"],
                    body=m["Body"],
                    attributes={
                        "attributes": m.get("Attributes", {}),
                        "message_attributes": m.get("MessageAttributes", {}),
                    },
                )
            )
        return out

    def delete(self, receipt_handle: str) -> None:
        self._client.delete_message(QueueUrl=self._queue_url, ReceiptHandle=receipt_handle)

    def change_visibility(self, receipt_handle: str, timeout_seconds: int) -> None:
        self._client.change_message_visibility(
            QueueUrl=self._queue_url,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=timeout_seconds,
        )

from app.schemas.protocol import WebSocketMessage


def test_websocket_protocol_schema_validation():
    message = WebSocketMessage.model_validate(
        {
            "type": "world.update",
            "payload": {
                "agents": {},
                "departments": {},
                "tasks": {},
                "events": [],
            },
        }
    )

    assert message.type == "world.update"
    assert message.payload["tasks"] == {}
    assert message.ts > 0

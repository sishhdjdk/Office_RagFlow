from flask import Blueprint
from api.apps import login_required

chat_bp=Blueprint("chat", __name__)

@chat_bp.route("/chats", methods=["POST"])
@login_required #role: user
def create():
    data=request.get_json(silent=true) or {}
    
        


@chat_bp.route("/chats", methods=["get"])


@chat_bp.route("/chats/:id", methods=["get"])

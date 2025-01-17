from flask import Blueprint, jsonify, abort, make_response, request
from app.models.task import Task
from app.models.goal import Goal
from app import db
from sqlalchemy import asc, desc
import datetime, requests, os
from dotenv import load_dotenv

load_dotenv()

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")

def validate_model(cls, model_id):
    try:
        model_id = int(model_id)
    except:
        abort(make_response({"message":f"{cls.__name__} {model_id} invalid"}, 400))

    model = cls.query.get(model_id)

    if not model:
        abort(make_response({"message":f"{cls.__name__} {model_id} not found"}, 404))

    return model


@tasks_bp.route("", methods=["GET"])
def read_all_tasks():
    title_query = request.args.get("title")
    sort_query = request.args.get("sort")
    
    if title_query:
        tasks = Task.query.filter_by(title=title_query)
        
    if sort_query == "asc":
        tasks = Task.query.order_by(Task.title.asc())
        
    if sort_query == "desc":
        tasks = Task.query.order_by(Task.title.desc())
        
    if not title_query and not sort_query:
            
        tasks = Task.query.all()
    
    
    tasks_response = []
    for task in tasks:
        tasks_response.append(
            {
                "id": task.task_id,
                "title": task.title,
                "description": task.description,
                "is_complete": False 
            }
        )
        
    return jsonify(tasks_response)
    


@tasks_bp.route("/<task_id>", methods=["GET"])
def read_one_task(task_id):
    task = validate_model(Task, task_id)
    
    if not task.goal_id:
        return jsonify({"task": task.to_dict()}), 200

    else:
        return jsonify({
            "task": {
                "id": task.task_id,
                "goal_id": task.goal_id,
                "title": task.title,
                "description": task.description,
                "is_complete": bool(task.completed_at)
            }}), 200
    


@tasks_bp.route("", methods=["POST"])
def create_task():
    request_body = request.get_json()
    if len(request_body) != 2:
        return jsonify({"details": "Invalid data"}), 400
    
    new_task = Task.from_dict(request_body)
    
    db.session.add(new_task)
    db.session.commit()

    return jsonify({"task": new_task.to_dict()}), 201


@tasks_bp.route("/<task_id>", methods=["PUT"])
def update_task(task_id):
    task = validate_model(Task, task_id)

    request_body = request.get_json()

    task.title = request_body["title"]
    task.description = request_body["description"]
    
    db.session.commit()
    
    return jsonify({"task": task.to_dict()}), 200
    


@tasks_bp.route("/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = validate_model(Task, task_id)

    db.session.delete(task)
    db.session.commit()
    
    return jsonify({"details": f'Task {task.task_id} "{task.title}" successfully deleted'}), 200


def slack_api_call(message):
    API_KEY = os.environ.get("SLACK_TOKEN")
    header = {"Authorization":API_KEY}
    URL = "https://slack.com/api/chat.postMessage"
    query_params = {"channel":"task-notifications", "text":message}

    requests.post(URL, params=query_params, headers=header)


@tasks_bp.route("/<task_id>/mark_complete", methods=["PATCH"])
def mark_complete_on_incomplete_task(task_id):
    task = validate_model(Task, task_id)
    task.completed_at = datetime.datetime.utcnow()
    
    db.session.commit()
    
    slack_api_call(f"Someone just completed the task {task.title}")
    
    return jsonify({"task": task.to_dict()})
    
    
@tasks_bp.route("/<task_id>/mark_incomplete", methods=["PATCH"])
def mark_incomplete_on_complete_task(task_id):
    task = validate_model(Task, task_id)
    task.completed_at = None
    
    db.session.commit()
    
    return jsonify({"task": task.to_dict()}) 


from flask import Blueprint, jsonify, abort, make_response, request
from app.models.task import Task
from app.models.goal import Goal
from app import db
from sqlalchemy import asc, desc
import datetime, requests, os
from dotenv import load_dotenv

load_dotenv()

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")
goals_bp = Blueprint("goals", __name__, url_prefix="/goals")

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
    
    # tasks_response = [task.to_dict() for task in tasks]
    


@tasks_bp.route("/<task_id>", methods=["GET"])
def read_one_task(task_id):
    task = validate_model(Task, task_id)
    
    if not task.goal_id:
        return jsonify({
            "task": {
                "id": task.task_id,
                "title": task.title,
                "description": task.description,
                "is_complete": bool(task.completed_at)
            }}), 200
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


# def slack_api_call(message):
#     token = os.environ.get("SLACK_API")
    
#     requests.post("https://slack.com/api/chat.postMessage", params={
#         "channel": "task-notifications", 
#         "text": message}, 
#                 headers={
#                     "Authorization": token
#         })

# def slack_api_call(message):
#     token = os.environ.get("SLACK_API")
#     PATH = "https://slack.com/api/chat.postMessage"
#     header = {
#         "Authorization": "Bearer" + token
#         }
    
#     query_params = {
#         "channel": "task-notifications",
#         "text": message
#     }
    
#     response = requests.post(PATH, data=query_params, headers=header)


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


##########################################
######           GOAL              #######
##########################################

@goals_bp.route("", methods=["GET"])
def read_all_goals():
    goals_response = []
    goals = Goal.query.all()
    
    for goal in goals:
        goals_response.append(goal.goal_dict())
    
    return jsonify(goals_response) 
    

@goals_bp.route("/<goal_id>", methods=["GET"])
def read_one_goal(goal_id):
    goal = validate_model(Goal, goal_id)
    
    return {"goal": goal.goal_dict()}, 200


@goals_bp.route("", methods=["POST"])
def create_goal():
    request_body = request.get_json()
    if "title" not in request_body:
        return make_response({
            "details": "Invalid data"}), 400
    
    new_goal = Goal(
        title=request_body["title"]
    )

    db.session.add(new_goal)
    db.session.commit()
    
    return {"goal": new_goal.goal_dict()}, 201


@goals_bp.route("/<goal_id>", methods=["PUT"])
def update_goal(goal_id):
    goal = validate_model(Goal, goal_id)
    request_body = request.get_json()
    
    return {"goal": goal.goal_dict()}, 200


@goals_bp.route("/<goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    goal = validate_model(Goal, goal_id)
    
    db.session.delete(goal)
    db.session.commit()
    
    return jsonify({"details": f'Goal {goal.goal_id} "{goal.title}" successfully deleted'}), 200


@goals_bp.route("/<goal_id>/tasks", methods=["POST"])
def post_tasks_to_goal(goal_id):
    goal = validate_model(Goal, goal_id)
    request_body = request.get_json()
    
    goal.tasks = []
    
    for task_id in request_body["task_ids"]:
        task = validate_model(Task, task_id)
        goal.tasks.append(task) 
    
        db.session.commit()
    
    return make_response(jsonify({
        "id": goal.goal_id,
        "task_ids": request_body["task_ids"]
    })), 200
    
    
@goals_bp.route("/<goal_id>/tasks", methods=["GET"])
def get_task_one_goal(goal_id):
    goal = validate_model(Goal, goal_id)
    tasks_response = []
    for task in goal.tasks:
        tasks_response.append({
                "id": task.task_id,
                "goal_id": goal.goal_id,
                "title": task.title,
                "description": task.description,
                "is_complete": bool(task.completed_at)
                
            }), 200
    return jsonify({
                "id": goal.goal_id,
                "title": goal.title,
                "tasks": tasks_response}), 200


    

        
    
    
    
    
    
    

    

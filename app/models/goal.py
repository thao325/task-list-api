from app import db

class Goal(db.Model):
    goal_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String)
    tasks = db.relationship("Task", back_populates="goal")
    
    def goal_dict(self):
        return {
            "id": self.goal_id,
            "title": self.title
        }
    # @classmethodcs
    # def from_dict(cls, req_body):
    #     return cls(
    #         title=req_body['title'],
    #     )
    

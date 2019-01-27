import time
import copy

import nandy.store.redis
import nandy.store.mysql
import nandy.store.graphite

class NandyData(object):
    """
    Main class for interacting with Nandy data
    We have lots of similar functions because it's easier to read with all the interdependecies
    """

    def __init__(self):

        self.speech = nandy.store.redis.Channel("speech")
        self.mysql = nandy.store.mysql.MySQL()
        self.graphite = nandy.store.graphite.Graphite()
        self.event = nandy.store.redis.Channel("event")

    # Person

    def person_create(self, fields):
        """
        Creates Person based on fields
        """
        
        person = nandy.store.mysql.Person(**fields)
        self.mysql.session.add(person)
        self.mysql.session.commit()

        return person

    def person_list(self, filter=None):
        """
        Lists Persons based on filter
        """

        if filter is None:
            filter = {}

        return self.mysql.session.query(
            nandy.store.mysql.Person
        ).filter_by(
            **filter
        ).order_by(
            nandy.store.mysql.Person.name
        ).all()

    def person_retrieve(self, person_id):
        """
        Retrieves Person based on id
        """

        return self.mysql.session.query(
            nandy.store.mysql.Person
        ).get(
            person_id
        )

    def person_update(self, person_id, fields):
        """
        Retrieves Person based on id and fields
        """

        rows = self.mysql.session.query(
            nandy.store.mysql.Person
        ).filter_by(
            person_id=person_id
        ).update(
            fields
        )
        self.mysql.session.commit()
        return rows

    def person_delete(self, person_id):
        """
        Deletes Person based on id
        """

        rows = self.mysql.session.query(
            nandy.store.mysql.Person
        ).filter_by(
            person_id=person_id
        ).delete()
        self.mysql.session.commit()
        return rows

    # Area

    def area_create(self, fields):
        """
        Creates Area based on fields
        """
        
        area = nandy.store.mysql.Area(**fields)
        self.mysql.session.add(area)
        self.mysql.session.commit()

        return area

    def area_list(self, filter=None):
        """
        Lists Areas based on filter
        """

        if filter is None:
            filter = {}

        return self.mysql.session.query(
            nandy.store.mysql.Area
        ).filter_by(
            **filter
        ).order_by(
            nandy.store.mysql.Area.name
        ).all()

    def area_retrieve(self, area_id):
        """
        Retrieves Area based on id
        """

        return self.mysql.session.query(
            nandy.store.mysql.Area
        ).get(
            area_id
        )

    def area_update(self, area_id, fields):
        """
        Retrieves Area based on id and fields
        """

        rows = self.mysql.session.query(
            nandy.store.mysql.Area
        ).filter_by(
            area_id=area_id
        ).update(
            fields
        )
        self.mysql.session.commit()
        return rows

    def area_status(self, area, current):
        """
        Sets an area's status
        """

        if area.status == current:
            return False

        area.updated = time.time()
        area.status = current
        self.mysql.session.commit()

        for status in area.data["statuses"]:
            if current == status["value"]: 
                self.graphite.send("area", area.name, "status", status["value"], 1, area.updated)
                if "chore" in status:
                    self.chore_create(template=status["chore"])
            else:
                self.graphite.send("area", area.name, "status", status["value"], 0, area.updated)
                
        return True

    def area_delete(self, area_id):

        rows = self.mysql.session.query(
            nandy.store.mysql.Area
        ).filter_by(
            area_id=area_id
        ).delete()
        self.mysql.session.commit()
        return rows

    # Template

    def template_create(self, fields):
        """
        Creates Template based on fields
        """
        
        template = nandy.store.mysql.Template(**fields)
        self.mysql.session.add(template)
        self.mysql.session.commit()

        return template

    def template_list(self, filter=None):
        """
        Lists Templates based on filter
        """

        if filter is None:
            filter = {}

        return self.mysql.session.query(
            nandy.store.mysql.Template
        ).filter_by(
            **filter
        ).order_by(
            nandy.store.mysql.Template.name, 
            nandy.store.mysql.Template.kind
        ).all()

    def template_retrieve(self, template_id):
        """
        Retrieves Template based on id
        """

        return self.mysql.session.query(
            nandy.store.mysql.Template
        ).get(
            template_id
        )

    def template_update(self, template_id, fields):
        """
        Retrieves Template based on id and fields
        """

        rows = self.mysql.session.query(
            nandy.store.mysql.Template
        ).filter_by(
            template_id=template_id
        ).update(
            fields
        )
        self.mysql.session.commit()
        return rows

    def template_delete(self, template_id):
        """
        Deletes Person based on id
        """

        rows = self.mysql.session.query(
            nandy.store.mysql.Template
        ).filter_by(
            template_id=template_id
        ).delete()
        self.mysql.session.commit()
        return rows

    # Speak

    def speak_chore(self, text, chore):
        """
        Says something on the speaking channel from a chore
        """

        # Follows the standards format

        message = {
            "timestamp": time.time(),
            "text": f"{chore.person.name}, {text}",
            "language": chore.data["language"]
        }

        if "node" in chore.data:
            message["node"] = chore.data["node"]

        self.speech.publish(message)
        chore.data["notified"] = time.time()
        chore.data["updated"] = time.time()

    def speak_task(self, text, task, chore):
        """
        Says something on the speaking channel
        """

        # Hit up chore and indicated we've been notified

        self.speak_chore(text, chore)
        task["notified"] = time.time() 

    # Remind

    def remind(self, data):

        # If it has a delay and isn't time yet, don't bother yet

        if "delay" in data and data["delay"] + data["start"] > time.time():
            return False

        # If it's paused, don't bother either

        if "paused" in data and data["paused"]:
            return False

        # If it has an interval and it's more been more than that since the last notification

        if "interval" in data and time.time() > data["notified"] + data["interval"]:
            return True

        return False

    def remind_task(self, chore):
        """
        Sees if any reminders need to go out for all tasks of a chore
        """

        for task in chore.data["tasks"]:

            # If this is the first active task

            if "start" in task and "end" not in task:
                
                if self.remind(task):

                    # Notify and sotre that we did

                    self.speak_task(f"please {task['text']}", task, chore)

                # We've found the active task, so regardless we're done

                break

    def remind_chore(self):
        """
        Sees if any reminders need to go out for all chores and people
        """

        for chore in self.mysql.session.query(nandy.store.mysql.Chore).filter_by(status="started"):

            if self.remind(chore.data):
                self.speak_chore(f"you still have to {chore.data['text']}", chore)

            if "tasks" in chore.data:
                self.remind_task(chore)

        self.mysql.session.commit()

    # Chore

    def chore_create(self, fields=None, template=None):
        """
        Creates a chore from a template
        """

        if template is None:
            template = {}

        if fields is None:
            fields = {}

        fields["status"] = "started"
        fields["created"] = time.time()
        fields["updated"] =  fields["created"]

        if "data" not in fields and template:
            fields["data"] = copy.deepcopy(template)

        if "name" in template and "name" not in fields:
            fields["name"] = template["name"]

        if "person" in template and "person_id" not in fields:
            fields["person_id"] = self.mysql.session.query(nandy.store.mysql.Person).filter_by(name=template["person"]).one().person_id

        if "language" not in fields["data"]:
            fields["data"]["language"] = "en-us"

        if "tasks" in fields["data"]:
            for index, task in enumerate(fields["data"]["tasks"]):
                if "id" not in task:
                    task["id"] = index

        # Create and save now because we need the db 
        # person set up and other things may go wrong

        chore = nandy.store.mysql.Chore(**fields)
        self.mysql.session.add(chore)
        self.mysql.session.commit()

        # We've start the overall chore.  Notify the person
        # record that we did so.

        chore.data["start"] = time.time()
        self.speak_chore(f"time to {chore.data['text']}", chore)

        # Check for the first tasks and set our changes. 

        self.chore_check(chore)
        self.mysql.session.commit()

        return chore

    def chore_list(self, filter=None):
        """
        Lists Chores based on filter
        """

        if filter is None:
            filter = {}

        return self.mysql.session.query(
            nandy.store.mysql.Chore
        ).filter_by(
            **filter
        ).order_by(
            nandy.store.mysql.Chore.created.desc()
        ).all()

    def chore_retrieve(self, chore_id):
        """
        Retrieves Chore based on id
        """

        return self.mysql.session.query(
            nandy.store.mysql.Chore
        ).get(
            chore_id
        )

    def chore_update(self, chore_id, fields):
        """
        Retrieves Chore based on id and fields
        """

        rows = self.mysql.session.query(
            nandy.store.mysql.Chore
        ).filter_by(
            chore_id=chore_id
        ).update(
            fields
        )
        self.mysql.session.commit()
        return rows

    def chore_check(self, chore):
        """
        Checks to see if there's tasks remaining, if so, starts one.
        If not completes the task
        """

        if "tasks" not in chore.data:
            return

        # Go through all the tasks

        for task in chore.data["tasks"]:

            # If there's one that's start and not completed, we're good

            if "start" in task and "end" not in task:
                return

        # Go through the tasks again now that we know none are in progress

        for task in chore.data["tasks"]:

            # If not start, start it, and let 'em know

            if "start" not in task:
                task["start"] = time.time()

                if "paused" in task and task["paused"]:
                    self.speak_task(f"you do not have to {task['text']} yet", task, chore)
                else:
                    self.speak_task(f"please {task['text']}", task, chore)

                return

        # If we're here, all are done, so complete the chore

        self.chore_complete(chore)

    def chore_next(self, chore):
        """
        Completes the current task and starts the next. This is used
        with a button press.  
        """

        # Go through all the tasks, complete the first one found
        # that's ongoing and break

        for task in chore.data["tasks"]:
            if "start" in task and "end" not in task:
                self.task_complete(task, chore)
                return True

        return False

    def chore_pause(self, chore):
        """
        Pauses a chore
        """

        # Pause if it isn't. 

        if "paused" not in chore.data or not chore.data["paused"]:

            chore.data["paused"] = True
            self.speak_chore(f"you do not have to {chore.data['text']} yet", chore)
            self.mysql.session.commit()

            return True

        return False

    def chore_unpause(self, chore):
        """
        Resumes a chore
        """

        # Resume if it's paused

        if "paused" in chore.data and chore.data["paused"]:

            chore.data["paused"] = False
            self.speak_chore(f"you do have to {chore.data['text']} now", chore)
            self.mysql.session.commit()

            return True

        return False

    def chore_skip(self, chore):
        """
        Skips a chore
        """

        # Skip if it hasn't been

        if "skipped" not in chore.data or not chore.data["skipped"]:

            chore.data["skipped"] = True
            chore.data["end"] = time.time()
            chore.status = "ended"
                
            self.speak_chore(f"you do not have to {chore.data['text']}", chore)
            self.mysql.session.commit()

            return True

        return False

    def chore_unskip(self, chore):
        """
        Unskips a chore
        """

        # Unskip if it has been

        if "skipped" in chore.data and chore.data["skipped"]:

            chore.data["skipped"] = False
            del chore.data["end"]
            chore.status = "started"

            self.speak_chore(f"you do have to {chore.data['text']}", chore)
            self.mysql.session.commit()

            return True

        return False

    def chore_complete(self, chore):
        """
        Completes a chore
        """

        if "end" not in chore.data or chore.status != "ended":

            chore.data["end"] = time.time()
            chore.status = "ended"
            self.speak_chore(f"thank you. You did {chore.data['text']}", chore)
            self.mysql.session.commit()
            self.graphite.send("person", chore.person.name, "chore", chore.data["text"], "duration", chore.data["end"] - chore.data["start"], chore.data["start"])

            return True

        return False

    def chore_incomplete(self, chore):
        """
        Uncompletes a chore
        """

        if "end" in chore.data or chore.status == "ended":

            del chore.data["end"]
            chore.status = "started"
            self.speak_chore(f"I'm sorry but you did not {chore.data['text']} yet", chore)
            self.mysql.session.commit()

            return True
        
        return False

    def chore_delete(self, chore_id):
        """
        Deletes Chore based on id
        """

        rows = self.mysql.session.query(nandy.store.mysql.Chore).filter_by(chore_id=chore_id).delete()
        self.mysql.session.commit()
        return rows

    # Task

    def task_pause(self, task, chore):
        """
        Pauses a task
        """

        # Pause if it isn't. 

        if "paused" not in task or not task["paused"]:

            task["paused"] = True
            self.speak_task(f"you do not have to {task['text']} yet", task, chore)
            self.mysql.session.commit()

            return True

        return False

    def task_unpause(self, task, chore):
        """
        Resumes a task
        """

        # Resume if it's paused

        if "paused" in task and task["paused"]:

            task["paused"] = False
            self.speak_task(f"you do have to {task['text']} now", task, chore)
            self.mysql.session.commit()

            return True

        return False

    def task_skip(self, task, chore):
        """
        Skips a task
        """

        # Pause if it hasn't been

        if "skipped" not in task or not task["skipped"]:

            task["skipped"] = True
            task["end"] = time.time()

            # If it hasn't been started, do so now

            if "start" not in task:
                task["start"] = task["end"]
                
            self.speak_task(f"you do not have to {task['text']}", task, chore)

            # Check to see if there's another one and set

            self.chore_check(chore)
            self.mysql.session.commit()

            return True

        return False

    def task_unskip(self, task, chore):
        """
        Unskips a task
        """

        # Unskip if has been

        if "skipped" in task and task["skipped"]:

            task["skipped"] = False
            del task["end"]
            self.speak_task(f"you do have to {task['text']}", task, chore)

            # And incomplete the overall chore too if needed

            if chore.status == "ended":
                chore.status = "started"
                del chore.data["end"]
                self.speak_chore(f"I'm sorry but you did not {chore.data['text']} yet", chore)

            # Save

            self.mysql.session.commit()

            return True

        return False

    def task_complete(self, task, chore):
        """
        Completes a specific task
        """

        # Complete if it isn't. 

        if "end" not in task:

            task["end"] = time.time()

            # If it hasn't been started, do so now

            if "start" not in task:
                task["start"] = task["end"]

            self.speak_task(f"you did {task['text']}", task, chore)
            self.graphite.send("person", chore.person.name, "chore", chore.data["text"], "task", task["text"], "duration", task["end"] - task["start"], task["start"])

            # See if there's a next one, save our changes

            self.chore_check(chore)
            self.mysql.session.commit()

            return True

        return False

    def task_incomplete(self, task, chore):
        """
        Undoes a specific task
        """

        # Delete completed from the task.  This'll leave the current task started.
        # It's either that or restart it.  This action is done if a kid said they
        # were done when they weren't.  So an extra penality is fine. 

        if "end" in task:
            del task["end"]
            self.speak_task(f"I'm sorry but you did not {task['text']} yet", task, chore)

            # And incomplete the overall chore too if needed

            if chore.status == "ended":
                chore.status = "started"
                del chore.data["end"]
                self.speak_chore(f"I'm sorry but you did not {chore.data['text']} yet", chore)

            # Don't check because we know one is started. But set out changes.

            self.mysql.session.commit()

            return True

        return False

    # Act

    def act_create(self, fields=None, template=None):
        """
        Creates an act from a template
        """

        if template is None:
            template = {}

        if fields is None:
            fields = {}

        fields["created"] = time.time()

        if "data" not in fields and template:
            fields["data"] = copy.deepcopy(template)

        if "name" in template and "name" not in fields:
            fields["name"] = template["name"]

        if "person" in template and "person_id" not in fields:
            fields["person_id"] = self.mysql.session.query(nandy.store.mysql.Person).filter_by(name=template["person"]).one().person_id

        if "value" in template and "value" not in fields:
            fields["value"] = template["value"]

        act = nandy.store.mysql.Act(**fields)

        # Save it

        self.mysql.session.add(act)
        self.mysql.session.commit()
        self.graphite.send("person", act.person.name, "act", act.name, 1 if act.value == "positive" else -1, act.created)

        # Check to see if we should fire off a chore

        if "chore" in template and act.value == "negative":
            self.chore_create({"person_id": fields["person_id"]}, template["chore"])

        return act

    def act_list(self, filter=None):
        """
        Lists Acts based on filter
        """

        if filter is None:
            filter = {}

        return self.mysql.session.query(
            nandy.store.mysql.Act
        ).filter_by(
            **filter
        ).order_by(
            nandy.store.mysql.Act.created.desc()
        ).all()

    def act_retrieve(self, act_id):
        """
        Retrieves Act based on id
        """

        return self.mysql.session.query(
            nandy.store.mysql.Act
        ).get(
            act_id
        )

    def act_update(self, act_id, fields):
        """
        Retrieves Act based on id and fields
        """

        rows = self.mysql.session.query(
            nandy.store.mysql.Act
        ).filter_by(
            act_id=act_id
        ).update(
            fields
        )
        self.mysql.session.commit()
        return rows

    def act_delete(self, act_id):
        """
        Deletes Act based on id
        """

        rows = self.mysql.session.query(
            nandy.store.mysql.Act
        ).filter_by(
            act_id=act_id
        ).delete()
        self.mysql.session.commit()
        return rows
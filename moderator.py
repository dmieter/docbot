from datetime import datetime

class Moderator:
    def __init__(self):
        self.daily_questions = {}
        self.bans = {}

    def is_question_allowed(self, user_id, config):
        today = datetime.today().strftime('%Y%m%d')
        print("current user: {} bans: {}".format(user_id,self.bans))
        if user_id in self.bans and self.bans[user_id] > today:
            print("{} забанен до {}".format(user_id, self.bans[user_id]))
            return False, "Извините, ваша возможность задавать вопросы ограничена. Обратитесь к администратору."     
        elif 'question_limit' not in config:
            return True, 1   
        elif user_id not in self.daily_questions:
            self.daily_questions[user_id] = {today : 1}
            return True, 1
        elif today not in self.daily_questions[user_id]:
            self.daily_questions[user_id][today] = 1
            return True, 1
        else:
            today_questions = self.daily_questions[user_id][today]
            if today_questions >= config['question_limit']:
              print("{} превысил лимит вопросов за {}".format(user_id, today))
              return False, "Извините, вы превысили лимит вопросов за сегодня."     
            else:
              today_questions = today_questions + 1
              self.daily_questions[user_id][today] = today_questions
              return True, today_questions

    def ban_user(self, user_id, date):
        if user_id not in self.bans:
            self.bans[user_id] = date 
        elif self.bans[user_id] < date:
            self.bans[user_id] = date

        print("{} заблокирован до {}".format(user_id, self.bans[user_id]))

    def unban_user(self, user_id):
        if user_id in self.bans:
            del self.bans[user_id]

        

from google.appengine.ext import ndb
from model import account

priceplan_data = {
             'plan_name': 'Basic Plan',
             'plan_price': 0,
             }

priceplan = account.PricePlan()
priceplan.populate(**priceplan_data)
priceplan.put()
 
userrole_data = [
                 {
                  'role_name': 'Team User',
                  'access_level': 10
                  },
                 {
                  'role_name': 'Team Admin',
                  'access_level': 50
                  },
                 {
                  'role_name': 'Group Admin',
                  'access_level': 100
                  },
                 {
                  'role_name': 'System Admin',
                  'access_level': 500
                  },
                 {
                  'role_name': 'Super Admin',
                  'access_level': 1000
                  },                                                   
                 ]

for each in userrole_data:
    userrole = account.UserRole()
    userrole.populate(**each)
    userrole.put()

#Change the Group Admin Permission
#Signup a new user
#Change the biz group status to 'Active'


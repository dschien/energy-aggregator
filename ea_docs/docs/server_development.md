
# Debugging
### REST Client

There are many REST clients around. The Chrome Advanced Rest Client is very good.

To test your setup try to access via `GET` [http://localhost:8000/api/device/1](http://localhost:8000/api/device/1) with a custom `Authorization` header with a value
`Token CHANGE_ME`, where you need to replace the token with a value you get from the admin
  interface `Token` model for your user account.
That user account needs to be in the groups that the relevant view (here `ep.apiviews.MeasurementList` specifies as its `required_groups` list.

You should be returned a list of measurements.

# Django Restframework

As you can see in the apiview import statement, the above fw is used to render DB models.
```
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAdminUser
```

It is advised to use this for additional APIs.
There is a lots of documentation [here](http://www.django-rest-framework.org/).


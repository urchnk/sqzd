# SQZD

Telegram-bot for scheduling appointments with barbers, tutors, etc + mini-CRM.
The stack is a prank that got out of control, please don't judge me for this.)
Django (models and ORM) + aiogram (TG bot logic)


### handling translations

`pybabel extract . -o locales/django.pot`

`pybabel update -d locales -D django -i locales/django.pot`

Update translations at this point

`pybabel compile --use-fuzzy -d locales -D django`

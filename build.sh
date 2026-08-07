#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py loaddata data.json

python manage.py shell -c "
from django.contrib.auth.models import User
for username, password in [
    ('djangoadmin', 'admin123'),
    ('sheila', 'sheila123'),
    ('dewa', 'dewa123'),
    ('noah', 'noah123'),
    ('fraud_test', 'fraud123'),
]:
    user = User.objects.filter(username=username).first()
    if user:
        user.set_password(password)
        user.save()
"

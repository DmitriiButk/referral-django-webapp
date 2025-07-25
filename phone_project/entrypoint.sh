#!/bin/sh

python manage.py migrate
exec "$@"

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
#!/bin/bash

celery -A tasks.tasks.celery worker -l INFO

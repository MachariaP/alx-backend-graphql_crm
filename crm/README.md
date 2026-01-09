# Celery Task Setup for CRM Reports

This guide explains how to set up Celery with Celery Beat to generate weekly CRM reports.

## Prerequisites

- Python 3.8+
- Django 3.2+
- Redis server

## Installation Steps

### 1. Install Dependencies

```bash
pip install celery django-celery-beat redis gql[requests]

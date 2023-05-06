from celery import shared_task
from django.utils import timezone
import logging
from flights.models import Flight, Ticket, Expiring

logger = logging.getLogger(__name__)


@shared_task
def flight_expiration_task(flight_id):
    logger.info(f"Запущена с изменением статуса рейса с ID {flight_id}")
    try:
        flight = Flight.objects.get(pk=flight_id)
        flight.expire = Expiring.EXPIRED
        flight.save()
        logger.info(f"Статус рейса с ID {flight_id} успешно изменен")
    except Flight.DoesNotExist:
        logger.warning(f"Рейс с ID {flight_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при изменении статуса рейса с ID {flight_id}: {e}")


@shared_task
def ticket_expiration_task(ticket_id):
    logger.info(f"Запущена задача изменения статуса билета с ID {ticket_id}")
    try:
        ticket = Ticket.objects.get(pk=ticket_id)
        ticket.expire = Expiring.EXPIRED
        ticket.save()
        logger.info(f"Успешно изменен статус с ID {ticket_id}")
    except Ticket.DoesNotExist:
        logger.warning(f"Билет с ID {ticket_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при изменении статуса билета с ID {ticket_id}: {e}")
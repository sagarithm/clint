import asyncio
from datetime import datetime, timedelta, timezone
from core.database import get_db
from core.config import settings
from core.logger import logger
from outreach.email_operator import EmailOperator

async def check_sla_breaches() -> None:
    """Check for reply events or leads that have breached the SLA."""
    async with get_db() as db:
        # Find leads in 'replied_positive' or 'replied_neutral' that haven't been moved for SLA_BREACH_HOURS
        breach_time = datetime.now(timezone.utc) - timedelta(hours=settings.SLA_BREACH_HOURS)
        breach_str = breach_time.strftime('%Y-%m-%d %H:%M:%S')

        query = """
            SELECT id, name, lifecycle_state, state_updated_at 
            FROM leads 
            WHERE lifecycle_state IN ('replied_positive', 'human_review_required')
            AND state_updated_at < ?
        """
        async with db.execute(query, (breach_str,)) as cursor:
            breaches = await cursor.fetchall()
            
        if breaches:
            msg = f"SLA Breach Alert: {len(breaches)} leads requiring attention for over {settings.SLA_BREACH_HOURS} hours.\n\n"
            msg += "\n".join([f"Lead ID: {b['id']} | Name: {b['name']} | Status: {b['lifecycle_state']}" for b in breaches])
            
            logger.error(msg)
            operator = EmailOperator()
            # Failsafe so we only alert if operator configuration is ready
            if operator.accounts:
                success = await operator.send(
                    to_email=settings.ALERT_EMAIL,
                    subject="🚨 SLA Breach Alert - Clint Operations",
                    body=msg
                )
                if success:
                    logger.info("SLA breach alert email dispatched.")
            else:
                logger.warning("Operator not configured, cannot send SLA breach email.")

async def sla_monitor_loop() -> None:
    """Continuous background loop for SLA monitoring."""
    logger.info("SLA Monitor background loop started.")
    while True:
        try:
            await check_sla_breaches()
        except Exception as e:
            logger.error(f"SLA Monitor error: {e}")
        
        # Check every hour
        await asyncio.sleep(3600)

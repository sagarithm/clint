import os
import shutil
from core.config import settings
from core.logger import logger

def reset_all_systems():
    """
    Performs a complete wipe of the local intelligence database and outreach history.
    This prepares the suite for a fresh launch.
    """
    logger.info("Initiating global system reset...")

    # 1. Clear Database
    db_path = settings.DB_PATH
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            logger.info(f"✓ Deleted database: {db_path}")
        except Exception as e:
            logger.error(f"✗ Failed to delete database: {e}")
    else:
        logger.info("! Database file not found, skipping.")

    # 2. Clear Screenshots
    screenshots_dir = "data/screenshots"
    if os.path.isdir(screenshots_dir):
        try:
            shutil.rmtree(screenshots_dir)
            os.makedirs(screenshots_dir)
            logger.info("✓ Cleared and re-initialized screenshots directory.")
        except Exception as e:
            logger.error(f"✗ Failed to clear screenshots: {e}")

    # 3. Clear Logs (Optional but recommended for full reset)
    log_file = "logs/outreach.log"
    if os.path.exists(log_file):
        try:
            open(log_file, 'w').close()
            logger.info("✓ Truncated outreach logs.")
        except Exception as e:
            logger.error(f"✗ Failed to clear logs: {e}")

    logger.info("System reset complete. Run server.py or run_outreach.py to re-initialize.")

if __name__ == "__main__":
    reset_all_systems()

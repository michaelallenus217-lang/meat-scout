from .safeway import scrape_safeway, get_everyday_prices as safeway_everyday
from .fredmeyer import scrape_fredmeyer, get_everyday_prices as fredmeyer_everyday
from .winco import scrape_winco, get_everyday_prices as winco_everyday
from .traderjoes import scrape_traderjoes, get_everyday_prices as traderjoes_everyday
from .thriftway import scrape_thriftway, get_everyday_prices as thriftway_everyday
from .costco import scrape_costco, get_everyday_prices as costco_everyday
from .commissary import scrape_commissary, get_everyday_prices as commissary_everyday

# Sale/ad scrapers (for email flyer)
SCRAPERS = {
    "safeway": scrape_safeway,
    "fredmeyer": scrape_fredmeyer,
    "winco": scrape_winco,
    "costco": scrape_costco,
    "traderjoes": scrape_traderjoes,
    "thriftway": scrape_thriftway,
    "commissary": scrape_commissary,
}

# Everyday price sources (for dashboard)
EVERYDAY = {
    "safeway": safeway_everyday,
    "fredmeyer": fredmeyer_everyday,
    "winco": winco_everyday,
    "costco": costco_everyday,
    "traderjoes": traderjoes_everyday,
    "thriftway": thriftway_everyday,
    "commissary": commissary_everyday,
}

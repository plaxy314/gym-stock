import logging
from gym.envs.registration import register

logger = logging.getLogger(__name__)

register(
    id='Stock-v0',
    entry_point='gym_stock.envs:StockEnv',
    timestep_limit=10000,
    reward_threshold=1.0,
    nondeterministic = True,
)

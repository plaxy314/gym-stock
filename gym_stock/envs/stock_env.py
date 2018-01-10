import os, subprocess, time, signal
import numpy as np
import gym
from gym import error, spaces
from gym import utils
from gym.utils import seeding

import logging
logger = logging.getLogger(__name__)

class StockEnv(gym.Env, utils.EzPickle):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        self.historical_returns = self._load_returns("SPY.csv")

        self.action_space = spaces.Discrete(20)
        self.observation_space = spaces.Box(-1.0, 1.0, (16,))
        self._seed()
        self.viewer = None
        self.state = None
        
    def __del__(self):
        pass
    
    def _configure_environment(self):
        """
        Provides a chance for subclasses to override this method and supply
        a different server configuration. By default, we initialize one
        offense agent against no defenders.
        """
        pass

    def _start_viewer(self):
        """
        Starts the SoccerWindow visualizer. Note the viewer may also be
        used with a *.rcg logfile to replay a game. See details at
        https://github.com/LARG/HFO/blob/master/doc/manual.pdf.
        """
        pass

    def _step(self, action):
        reward = self._take_action(action)
        if self.index >= len(self.surface[0]) - 96:
           ob = np.zeros((16,))
           ob[0] = self.score
           print("finish at step  %d: %.4f baseline, score %.4f --- actions %d leverage %.4f" %(self.index, self.baseline,self.score, self.total_actions, self.leverage))
           return ob, self.score, True, {}
            
        self.index += 96
        ob = self._observe()
        if self.index > 252 and self.score < 0.25:
            print("abort at step  %d: baseline %.4f , score %.4f < 0.25 --- actions %d, leverage %.4f" %(self.index, self.baseline,self.score, self.total_actions, self.leverage))
            return ob, 0, True, {}
       
        return ob, 0, False, {}
    
    def _take_action(self, action):
        """ Converts the action space into an HFO action. """
        if action:
            self.total_actions += 1
        self.leverage += ACTION_LOOKUP[action]
        if self.leverage > 3:
            self.leverage = 3
        if self.leverage < 0:
            self.leverage = 0
        
        next = self.index+96
        if  next < len(self.surface[0]):
            for i in range(self.index, next):
                r = self.surface[0][i]
                self.baseline *= (1+r)
                self.managed *= (1 + r*self.leverage)

        self.score = self.managed / self.baseline
        #print("step  %d: baseline %.4f , managed %.4f leverage %.4f" %(self.index, self.baseline, self.managed, self.leverage))

   
    def _reset(self):
        """ Repeats NO-OP action until a new episode begins. """
        intervals = 14
        days =  2**(intervals - 1)  # ~32 years
        slices = 2**(intervals - 2)           # ~16 years
        
        synthetical_returns = [[],[]]   
        high = len(self.historical_returns[0]) - slices
        for i in range(4):
            start = self.np_random.randint(0, high)
            for j in range(slices):
                synthetical_returns[0].append(self.historical_returns[0][start + j])
                synthetical_returns[1].append(self.historical_returns[1][start + j])
                    
        prices = [
            self._build_prices(synthetical_returns[0]),
            self._build_prices(synthetical_returns[1]),
            ]
        
        self.total_actions = 0
        self.index = 0
        self.leverage = 1.0
        self.managed = 1.0
        self.baseline = 1.0
        self.score = 1.0
        self.surface = self._build_surface(prices, days, intervals, days)
        return self._observe()
    
    def _observe(self):
        ob = np.zeros((16,))
        ob[0] = self.score
        ob[1] = self.surface[1][self.index]
        for i in range(14):
            ob[i+1] = self.surface[i][self.index]
        return ob        

    def _abspath(self, file):
        my_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(my_path, file)
        
    def _load_returns(self, csv):
        """ Load historical prices from a CSV file w/ the following headers.
            Date,Open,High,Low,Close,Adj Close,Volume
        """
        opening = []
        closing = []
        f = open(self._abspath(csv))
        for line in f.readlines():
            d, o, h, l, c, adj, v = line.split(',')
            if d == 'Date':
                continue
            opening.append(float(o))
            closing.append(float(adj))
        f.close()
        
        return [self._daily_returns(opening), self._daily_returns(closing)]    
  
    def _daily_returns(self, prices):
        """ Computes daily returns given daily prices. """
        returns = []
        returns.append(0)
        for i in range(1, len(prices)):
            r = prices[i] / prices[i - 1] - 1.0
            returns.append(r)            
        return returns
     
    def _build_prices(self, returns, start=1.0):
        """ Builds normalized price series based on daily returns. """
        prices = []
        for r in returns:
            start = start * (1 + r)
            prices.append(start)
        return prices     
     
    def _build_surface(self, prices, offset, intervals, days):
        """ Builds a return surface based on the prices. """
        assert len(prices) == 2 and len(prices[0]) == len(prices[1])
        assert len(prices[0]) >= (offset + days)
        opening = prices[0]
        closing = prices[1]

        surface = np.zeros((intervals + 2, days))
        # opening and closing return on day 0
        for j in range(days):
            d = offset + j            
            # closing price on day 0, unobservable at day 0
            surface[0][j] = closing[d] / closing[d-1]  - 1.0
            # return of opening price, observable by agent on day 0
            surface[1][j] = opening[d] / closing[d-1]  - 1.0

        # average daily returns over [1, 2^intervals) trading days, observable by agent on day 0
        for i in range(intervals):
            interval = 2**i
            for j in range(days):
                d = offset + j
                surface[i+2][j] = (closing[d]/closing[d-interval])**(1.0 / days) - 1.0
         
        return surface       
            
    def _render(self, mode='human', close=False):
        """ Viewer only supports human mode currently. """
        pass
    
    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

ACTION_LOOKUP = {
    0 : 0,
    1 : -0.25,
    2 : +0.25,
    3 : 0,
    4 : 0,
    5 : 0,
    6 : 0,
    7 : 0,
    8 : 0,
    9 : 0,
    10 : 0,
    11 : 0,
    12 : 0,
    13 : 0,
    14 : 0,
    15 : 0,
    16 : 0,
    17 : 0,
    18 : 0,
    19 : 0,
}

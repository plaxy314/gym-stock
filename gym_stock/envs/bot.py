import os, time

# test
class Bot():
    
    def __init__(self):
        self.historical_returns = self._load_returns("spy.csv")

    def run(self):
        p = 16.6
        px = p * 2.1
        hwm = p    # high water mark
        cr = .3   # cash ratio 
        asset = p  # initial asset
        stock = asset * (1- cr)
        cash =  asset * cr
        recovered = True
        count = 0
        total = 0
        down = 0
        last_hwm = 0
        last_hwm_asset = asset
        for i in range(len(self.historical_returns[1])):
            d = self.historical_returns[0][i]
            r = self.historical_returns[1][i]
            p *= (1+r)
            px *= (1+2.1*r)
            stock *= (1+3*r)
            asset = stock + cash
            if asset > last_hwm_asset:
               last_hwm_asset = asset
            total+=1
            if p > hwm:
              hwm = p
              count+=1
              if hwm >= last_hwm * 1.3:
                  last_hwm = 0
                  delta = asset * cr - cash
                  stock -= delta
                  cash += delta
                  print(d, "rebalance px:", px, " r:", asset/px, " stock ", stock, " ->", delta, "-> cash:", cash)
            else:
              drawdown = (p - hwm) / hwm
              if drawdown <= -0.30:
                   down +=1
                   pc = -100 * drawdown - 20
                   left =  last_hwm_asset * cr * (1 - (pc*pc) /400)
                   delta = cash - left
                   if left > 0 and delta > 0:
                       last_hwm = hwm
                       stock += delta
                       cash -= delta
                       print(d, "releverage px:", px , " r:", asset/px, " stock ", stock, "<-", delta, "<- cash:", cash)
                  
        print(count, "#####", down, "===", total)
        print(p, "#####", asset, ":", asset/p, " 2.1x:", px, ", ", px/p)

    def _abspath(self, file):
        my_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(my_path, file)
        
    def _load_returns(self, csv):
        """ Load historical prices from a CSV file w/ the following headers.
            Date,Open,High,Low,Close,Adj Close,Volume
        """
        opening = []
        closing = []
        date = []
        f = open(self._abspath(csv))
        for line in f.readlines():
            d, o, h, l, c, adj, v = line.split(',')
            if d == 'Date':
                continue
            date.append(d)
            opening.append(float(o))
            closing.append(float(adj))
        f.close()
        
        return [date, self._daily_returns(opening), self._daily_returns(closing)]    
  
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
    

Bot().run() 

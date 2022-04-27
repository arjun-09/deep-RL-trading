from lib import *
from scipy.signal import argrelextrema

# by Xiang Gao, 2018
# modified by Arjun Chouhan, 2022


def find_ideal(p, just_once, direction=1.):
    if not just_once:
        maximas = argrelextrema(p, np.greater)[0]
        minimas = argrelextrema(p, np.less)[0]
        reward = 0

        if len(minimas) > 0 and len(maximas) > 0:
            if maximas[0] < minimas[0] and p[0] < p[maximas[0]]:
                minimas = np.insert(minimas, 0, 0)
            elif maximas[0] > minimas[0] and p[0] > p[minimas[0]]:
                maximas = np.insert(maximas, 0, 0)
        elif len(minimas) > 0:
            maximas = np.insert(maximas, 0, 0)
            maximas = np.append(maximas, len(p) - 1)
        elif len(maximas) > 0:
            minimas = np.insert(minimas, 0, 0)
            maximas = np.append(minimas, len(p) - 1)
        else:
            a = p[0]
            b = p[len(p) - 1]

            if a < b:
                maximas = np.append(maximas, len(p) - 1)
                minimas = np.append(minimas, 0)
            elif a > b:
                minimas = np.append(minimas, len(p) - 1)
                maximas = np.append(maximas, 0)
            else:
                return 0
            

        print(maximas, minimas)

        for i in range(0, min(len(maximas), len(minimas))):
            
            if i >= len(maximas) and i < len(minimas):
                reward += abs(p[minimas[i]] - p[maximas[i - 1]])
            elif i < len(maximas) and i >= len(minimas):
                reward += p[maximas[i]] - p[minimas[i - 1]]
            else:
                reward += p[maximas[i]] - p[minimas[i]]
                if i + 1 < len(minimas):
                    reward += p[maximas[i]] - p[minimas[i + 1]]
                elif i + 1 < len(maximas):
                    reward += p[maximas[i + 1]] - p[minimas[i]]

        return reward

#        if direction > 0:
#            diff = np.array(p[1:]) - np.array(p[:-1])
#        else:
#            diff = -1. * (np.array(p[1:]) - np.array(p[:-1]))

#        return sum(np.maximum(np.zeros(diff.shape), diff))
    else:
        best = 0.
        i0_best = None
        for i in range(len(p)-1):
            if direction > 0:
                best = max(best, max(p[i+1:]) - p[i])
            else:
                best = max(best, -1. * (min(p[i+1:]) - p[i]))

        return best


class Market:
    """
    state           DEMA of prices, normalized using values at t
                    ndarray of shape (window_state, n_instruments * n_DEMA), i.e., 2D
                    which is self.state_shape

    action          five actions
                    0:    empty, don't open/close. 
                    1:    open a Long position
                    2:      open a Short position
                    3:     keep a Long/Short position
                    4:      close a Long/Short position     
    """
    
    def reset(self, rand_price=True):
        self.empty = True

        if rand_price:
            prices, self.title = self.sampler.sample()
            price = np.reshape(prices[:,0], prices.shape[0])

            self.prices = prices.copy()
            self.price = price/price[0]*100
            self.t_max = len(self.price) - 1

            profit = find_ideal(self.price[self.t0:], False)
#            downwards_profit = find_ideal(self.price[self.t0:], False, -1.0)

#            if downwards_profit > upwards_profit:
#                self.direction = -1.
#                self.max_profit = downwards_profit
#            else:
#                self.direction = 1.
#                self.max_profit = upwards_profit
            self.max_profit = profit

        self.t = self.t0
        return self.get_state(), self.get_valid_actions()


    def get_state(self, t=None):
        if t is None:
            t = self.t
        state = self.prices[t - self.window_state + 1: t + 1, :].copy()
        for i in range(self.sampler.n_var):
            norm = np.mean(state[:,i])
            state[:,i] = (state[:,i]/norm - 1.)*100    
        return state

    def get_valid_actions(self):
        if self.empty:
            return [0, 1, 2]    # do nothing, long, short
        else:
            return [3, 4]            # close, keep


    def get_noncash_reward(self, t=None, empty=None, closed=False):
        if t is None:
            t = self.t
        if empty is None:
            empty = self.empty
            if not closed:
                reward = self.direction * (self.price[t+1] - self.price[t])
            else:
                reward = self.direction * (self.price[t] - self.open_price)
        if empty:
            reward -= self.open_price
        if reward < 0:
            reward *= (1. + self.risk_averse)

        return reward


    def step(self, action):

        done = False
        if action == 0:        # Do nothing
            reward = 0.
            #self.empty = True
        elif action == 1:    # Long
            self.direction = 1.
            reward = self.get_noncash_reward()
            self.empty = False
            self.open_price = self.price[self.t]
        elif action == 2:    # Short
            self.direction = -1.
            reward = self.get_noncash_reward()
            self.empty = False
            self.open_price = self.price[self.t]
        elif action == 3:       # Keep
            reward = self.get_noncash_reward()
        elif action == 4:       # Close position
            reward = self.get_noncash_reward(closed=True)
            self.empty = True
        else:
            raise ValueError('no such action: '+str(action))

        self.t += 1
        return self.get_state(), reward, self.t == self.t_max, self.get_valid_actions()


    def __init__(self, 
        sampler, window_state, open_cost,
        direction=1., risk_averse=0.):

        self.sampler = sampler
        self.window_state = window_state
        self.open_price = open_cost
        self.direction = direction
        self.risk_averse = risk_averse

        self.n_action = 5
        self.state_shape = (window_state, self.sampler.n_var)
        self.action_labels = ['empty','long','short','keep','close']
        self.t0 = window_state - 1


if __name__ == '__main__':
    test_env()

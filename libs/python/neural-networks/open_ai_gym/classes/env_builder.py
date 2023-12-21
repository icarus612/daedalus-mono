import gymnasium as gym
import time
import sys
class EnvBuilder:
  def __init__(self, env, render_mode="human", seed=False):
    self.env = gym.make(env, render_mode=render_mode)
    self.seed = seed
  
  def load_env(self):
    current_seed = self.seed
    if not current_seed:
      current_seed = int(time.time())
    self.env.reset(seed=current_seed)
    self.env.render()
    
  def attempt(self, action_func):
    done = False
    truncated = False
    observation = False
    reward = False
    while not done and not truncated:
      action = action_func(observation, reward)
      observation, reward, done, truncated, info = self.env.step(action)
      if info not in [None, {}]:
        print(info)
  
  def test(self):
    self.attempt(self.env.action_space.sample)
    
  def cycle(self, action, cycles=5):
    for _ in range(cycles):
      self.load_env()
      self.attempt(action)
      
    self.env.close()
    
if __name__ == "__main__":
  env = sys.argv[1] if len(sys.argv) > 1 else "CartPole-v1"
  env_builder = EnvBuilder(env)
  env_builder.test()
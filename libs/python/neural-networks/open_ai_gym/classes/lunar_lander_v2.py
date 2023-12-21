import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from env_builder import EnvBuilder

class LunarLanderV2:
	def __init__(self):
		self.env = EnvBuilder("LunarLander-v2")
		self.Q = {}
		self.alpha = 0.1
		self.gamma = 0.9
		self.epsilon = 0.1
		self.total_reward = 0
		initial_observation = self.env.env.reset()
		if isinstance(initial_observation, dict):
			self.obs = {k: np.around(v, 1) for k, v in initial_observation.items()}
		elif isinstance(initial_observation, (list, tuple)):
			self.obs = tuple(np.around(v, 1) if not isinstance(v, dict) else {k: np.around(val, 1) for k, val in v.items()} for v in initial_observation)
		else:
			self.obs = np.around(initial_observation, 1)
	def build_model(self):
		model = Sequential()
		model.add(Dense(32, input_shape=(8,), activation="relu"))
		model.add(Dense(32, activation="relu"))
		model.add(Dense(self.env.action_space.n, activation="linear"))
		model.compile(loss="mse", optimizer=Adam())
		return model		
	
	def train(self, observation, action, reward, next_observation, done):
		target = reward
		if not done:
			target = (reward + self.gamma * np.amax(self.model.predict(np.array([next_observation]))[0]))
		target_f = self.model.predict(np.array([observation]))
		target_f[0][action] = target
		self.model.fit(np.array([observation]), target_f, epochs=1, verbose=0)
		
	def action(self, observation, reward):
		if np.random.random() > self.epsilon:
			return max(self.Q.get(self.obs, {0: 0, 1: 0}), key=self.Q.get(self.obs, {0: 0, 1: 0}).get)
		else:
			return self.env.action_space.sample()

	def cycle (self, cycles=5):
		self.env.cycle(self.action, cycles)
	
if __name__ == "__main__":
	llv2 = LunarLanderV2()
	llv2.cycle()

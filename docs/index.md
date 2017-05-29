---
layout: default
title:  Home
---

# Summary #
An application of reinforcement learning to a scuba diving agent in Minecraft. Four our project, we implement a Q-learning agent that is completely submerged in a water world. In each episode, the agent or in this case our scuba diver will dive and exploring looking for treasures hidden throughout the map with one caveat, it has no real scuba diving equipment. Without any additional equipment the agent has to rely on it's maximum capacity of air. This means the amount of air it has is very limited. So, it will have to made decisions based on its current air supply and decide whether its worthwhile to explore and find more treasure or to proceed on to finding more air and live. We attempt to expand on the Q-learning algorithm to the double Q-learning algorithm to solve the known problem of maximum bias with a single Q-learner. We expect to run into problems with too many actions that will cause the optimal policy to never converge. To solve this problem, we will attempt to implement some form of function approximation. Overall, this project was a very fun experience to learn about the applications reinforcement learning and it's various properties.

# Images/screenshots # 
<img src="https://i.ytimg.com/vi/FrwU_yNNFZk/maxresdefault.jpg" width="400px">
# Code repository #
- [code repository](https://github.com/andrewdoh/scuba_diver)

# Referenced resources # 
### Book ###
- [Sutton and Barto: Introduction to Reinforcement Learning](http://incompleteideas.net/sutton/book/bookdraft2016sep.pdf)

### Minecraft ###
- [Malmo Github](https://github.com/Microsoft/malmo) 

- [Malmo Gitter](https://gitter.im/Microsoft/malmo) 

- [Malmo API Documentation](https://microsoft.github.io/malmo/0.21.0/Documentation/index.html) 

### Research articles and etc. ###
- [Q-learning wikipedia article](https://en.wikipedia.org/wiki/Q-learning) 

- [Double Q-learning summary](https://hadovanhasselt.files.wordpress.com/2015/12/doubleqposter.pdf) 

- [Double Q-learning research article](https://papers.nips.cc/paper/3964-double-q-learning.pdf) 



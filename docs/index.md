---
layout: default
title:  Home
---

# Summary #
An application of reinforcement learning to a water biome in Minecraft. Our group implements a Q-learning agent that is completely submerged in a water world. In each episode, the agent or in this case our scuba diver will dive and exploring looking for treasures hidden throughout the map with one caveat, it has no real scuba diving equipment. This means the amount of air it has is very limited, so, it will have to made decisions based on its current air supply whether its worthwhile to explore and find more treasure or to find air and survive. We attempt to expand on the Q-learning algorithm to the double Q-learning algorithm to solve the problem of maximum bias with a single Q-learner. we expect to run into problems with too many actions that will cause the optimal policy to never converge. To solve this problem, we will attempt to implement some form of function approximation. Overall, this project has some very interesting problems and was a very fun to learn about the applications reinforcement learning and it's various properties.
# Images/screenshots # 
# Code repository #
[code repository](https://andrewdoh.github.io/scuba_diver/)
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



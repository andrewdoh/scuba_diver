---
layout: default
title: Status
---

### Technical Description ###
## Project Summary ##
When we first began formulating an idea for the project, we initially wanted to teach the agent to learn how to shoot a air and bow efficiently using a convulutional neural network. We dove in head first trying to learn all we could about how to use a CNN with minecraft. However, as time progressed, we began to see we were way out of our depths in terms of knowledge about an already very complex model. So, we had to revaluate our goals and decided it was best to reduce the complexity of our project but still have an interesting idea to apply to minecraft. With the class being about reinforcement learning, we thought it would a be cool idea to use Q-learning as the basis of our project. The general idea is to use a single Q-learning algorithm and let the agent learn and gather data. Then, we will implement double Q-learning algorithm to fix the inefficienies with just a single Q-learning algorithm. Once this is done we will make a comparison of the two types, highlighting the pros, cons and differences between them. A more general explanation of our new project from the minecraft perspective is an agent that explores a 3D underwater maze in search treasure but with a limited amount of resources. This might sounds like assignment 2 but there are some key differences to which we apply the algorithm and variables that provide for some very interesting problems. The first problem being that to navigate a 3D maze, we must allow the agent to move in 3 dimensions. Instead of having the 4 standard states (forward, backward, left, right), we now have 6 states which includes moving up and moving down. The second major difference is that we introduced a new resource that needs to be managed by the agent in the form of air. Now, the agent has to decided whether it has enough air to keep exploring and find more treasure or to reach the goal without drowning. Currently, our group is testing the agent with only two floors enabled because it is more effecient for testing our algorithm and it has a state space large enough for us to understand its scale but small enough so that it won't take us a long time to get the agent to final goal. 
## Approach ##
## Evaluation ##
## Remaining Goals and Challenges ##
### Algorithm ###
$$ Q(s_t,a_t)  \leftarrow \underbrace{Q(s_t,a_t)}_{\text{old value}} + \underbrace{\alpha_t}_{\text{learning rate}} \cdot \Bigg(\overbrace{\underbrace{r_{t} + 1}_{\text{reward}}  \underbrace{\gamma}_{\text{discount factor}} \cdot \underbrace{\max\limits_{a} Q(s_{t+1},a)}_{\text{estimate of optimal future value}}}^{\text{learned value}}   - \underbrace{Q(s_t,a_t)}_{\text{old value}}  \Bigg)$$


$$ Q_{1}(s_t,a_t)  \leftarrow \underbrace{Q_{1}(s_t,a_t)}_{\text{old value}} + \underbrace{\alpha_t}_{\text{learning rate}} \cdot \Bigg(\overbrace{\underbrace{r_{t} + 1}_{\text{reward}} +  \underbrace{\gamma}_{\text{discount factor}} \cdot Q_{2}(\underbrace{\max\limits_{a} Q_{1}(s_{t+1},a)}_{\text{estimate of optimal future value}}}^{\text{learned value}})   - \underbrace{Q_{1}(s_t,a_t)}_{\text{old value}}  \Bigg)$$

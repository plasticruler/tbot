# Introduction
This is the contribution guide for developers whishing to make contributions to our open-source project. You will find information about tools, processes, design and importantly the aim of the project. Please be sure to familiarise yourself with it.

# Objective of the project
In this project we are writing a bot called @distractobot. Its purpose to sit on a channel and post content to the channel according to some schedule, process reactions to posts and manage the type of posts that get sent.

We source content from a number of providers. The post schedule is hourly, and the content is selected at random.

# Tools / Setup
__VERY IMPORTANT: THE DEVELOPMENT TEAM USES A COMBINATION OF WINDOWS AND LINUX SO TOOLING MUST TAKE COGNISANCE OF THAT__
## pip/virtualenv
We will use virtual environments and the pip package manager to install and manage any depedencies.

## Celery
Celery is a task-processing queue. We use reddis as the backend (through a docker image). Tasks that are processed by the celery are tasks best suited for asynchonrous execution where the task is not time-sensitive and the result is trivial. For example `sendEmail` is a perfect method which can be wrapped into a task. We push the request onto a queue, and the celery picks up the task when the CPU becomes available according to the queue priority.
# Communication
We will use Telegram for communication.
# Processes
* We will use the git project board to manage and track tasks.
* We will use trunk-based developement. Please create a release/<feature> branch to do your work in. Commit to master only after a code-review.
# People

# Standards
* Variables should follow camelCasing.
* Class names should follow ProperCasing.
* Methods which return a value should begin with the `Get`, or other a verb such as `Do` or `Process` or `Handle`. 



 

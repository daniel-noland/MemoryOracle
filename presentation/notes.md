CSCI3308 Final Presentation
===========================

Spring 2015
-----------

### Methods

* Agile: only option for this project.

It was not clear that our goal was attainable when we started, and so waterfall made no sense.

Overall score: 5 (I suppose, since we could not really have done anything else)

* Test driven development: this was useful, but had limited application in a project so experimental.

Question: How do you write tests to specify functionality when the characteristics of your tools are unknown?

Answer: you iterate more frequently, experiment -> write test -> write code -> repeat <!-- make a graphic of this procedure -->

Overall score: 3 (writing tests for experimental functions can be a waste of time)

* Pair programming:

Learning the tools was half the battle!  Pair programming helps a lot.

Overall score 4 (sometimes this devolves into a time wasting exercise)

### Tools

We used MANY tools for this project.  Here are some of the most important ones:

#### Development tools:

##### Text editor / IDE

* Vim

Score 5/5 (but it is a 6 in our hearts)

* Webstorm

Score ? (I didn't really use it)

* Vim python mode

This is a big help to python vets.  Pulls up python documentation from inside vim!

##### VCS

* Git

Score 5 (also a 6 in our hearts)

* Github

Score 5 (nearly perfect for our needs)

* Fugitive

Vim plugin to control git!.

Score 5 (All hail Tim!)

##### Communication / organization aids:

* Trac

This is total overkill for a project of our size.  Filling out a ticket is slower than jumping into chat or mumble.  That said, the tool works quite well for larger projects / teams. <!-- show graph from trac here -->

Score 3

* Skype

Skype fails constantly.  Might work better on a less bandwidth constrained network.

Score 2

* Mumble

Mumble is where the real communication happed.  Perfect tool.

Score 5

* ssh + tmux

Allowed us to share a terminal so we could share ideas and teach each other.

Score 5

##### Programming languages / Libraries / compilers

* GCC

Provides an abundance of debugging information if you compile with -ggdb3 flag.  This fact is poorly documented and little known.

Score 4

* Python 3.4

Our favorite interpreted language, and the only one sporting GDB api.  Perfect in almost every way.

Score 5 

* GDB Python api

This is insanely powerful, but documentation is sparse / out of date.  We sometimes needed to look at source code to figure out functionality.  Very ill suited to mass data serialization, resulting in ponderously complex code base (2-3k lines of highly recursive python required).  To be fair, these features are new, and the problem they are meant to solve is very difficult.

Score 3

* LESS

Can't do css theming efficiently without this!

Score 4

* jQuery / jQuery UI

Not an optional part of web development these days.  You simply must use it.

Score 5

* d3

With the exception of jQuery, this is the highest quality javascript library we have ever seen.  Can produce stunning graphs.

Score 5

* Mongoengine / pymongo

Far simpler than django, and more effective when ODM is a better option than ORM.  We hope to see these two projects merge in the future.  Missing a few field types, and required significant work to install.

Score 4

##### Databases

We considered MySQL, PostgreSQL, sqlite, and Mongodb for this project, and settled on Mongodb.  SQL essentially insists on a data schema and we simply don't / can't have one.  Unfortunately, far more support is available for SQL than NoSQL.

Mongodb: 4

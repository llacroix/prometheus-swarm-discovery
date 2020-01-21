Contributing
============

Bug fixes:
==========

In order to help fixing bugs in this project, make sure that any pull request doesn't reduce the code coverage
and that any fixes to a bug has a test to prevent such bug from resurfacing later. Each new piece of code should
be covered by tests also.

New Features or improvements
============================

Before submitting any kind of new feature, first submit an issue with what problem that feature would actually
solve. That way, we can discuss how this could be implemented or may be it's possible to do without implementing
a drastic change to the codebase. 

Some guidelines to follow for new features:


1. Features should be generic enough that it doesn't solve a specific scenario.

For example, if you need to have the Node on which the service is running in a label, it wouldn't be
very wise to export that as a label. This project try to output exactly the labels without having to
post process them in prometheus relabel config. 

So any label choice should be opt-in.

2. Codebase should be kept as simple as possible. This service is by itself very simple.

While this service discovery does a little bit more than simply discovering services, it isn't doing any magic.
For example, it doesn't assume anything on where prometheus is being hosted or how it is running. So I don't think
having the service discovery trying to manage services in docker will ever be supported. All it does is read the state
of a system in a way prometheus can use it to scrape configs. It will never create destroy services/containers or connect
disconnect services from a network. 

3. Check if there are any feature I'd like to have implemented but for personal reason I couldn'T attack the issue yet. 

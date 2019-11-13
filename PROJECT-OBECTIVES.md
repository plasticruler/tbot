# Project Objectives
## Phase 1
In this part the general infrastructure to support the main functionality of bot was written. This part is in production.
### Features
* Content is downloaded from a single provider, namely reddit.
* Content can be refreshed through a flask-based UI.
* Subscriber topics can be managed through the same UI.
## Phase 2
In this phase the primary objective is to refactor the code so that we can add additional providers. 
### Technical debt from Phase 1
The development team has identified several major flaws in the code-base mainly having to do with the assumption that reddit was always going to be the only supported provider.
* The bot knows too much about what a reddit content item is. The coupling is too high. If we are to add additional providers, we need add an additional layer between a content item and what the bot knows about.
* The UI knows too much about what a reddit content update is. It should merely trigger an update.
* The code for reddit content management (retrieving content items, creating content items and so on should be moved to its own namespace) and ideally classes.
### Objectives of Phase 2
1. Wrap the content provider functionality into their own classes. Use base classes for common functionality, and interfaces so that outside services can invoke the classes.
2. Update the UI so that we can trigger content updates for the reddit provider using the new classes.
3. Update the content posting code so that the bot doesn't need to know about what the reddit content looks like.
4. Create a service so that 'random' is just a configuration feature for how content is returned. (We want to be able to sequence content in future.)
5. To test our revised design we will add XKCD as a new content provider. XKCD is quite simple. It has a payload with a pointer to a single type of resource (an image), and the title for this resource is part of the payload.
## Phase 3
In this phase the primary objective is to expand point 4 from Phase 2 so that we can create content-decks that are collections of content items that are dispatched in a sequence.
### Objectives of Phase 3
1. Update the UI so that a user can create content items.
2. Update the UI so that a user can tag collections of items as belonging to a deck, and let them sequence the items in the deck. The user must select from existing content items (which he could have created himself or may have been pre-existing)
3. Update the bot so that it dispatches the items in this deck in the defined sequence. This implies that the UI allows the user to specify the schedule / repeats.  

## Phase 4
In this phase the primary objective is to build on the idea of the deck and add custom reaction buttons to posts.
### Objectives of Phase 4
1. For a content deck we will associate a set of reaction buttons.
2. We will ensure that we are saving user reactions to posts through these reaction buttons.

def next(): print("\n")

next()

print("Hello and welcome to the PyTLEX demo!")
print("Let's start by building a couple graphs...")

next()

print("Now we created 2 graph objects. The first from wall street journal 6 and the other from 26.")
print("These are both self contained objects that are being held in memory.")
print("One thing to note is that, when those graphs got built, all the processing was done. Including: (list)")
print("Which took exactly (time)")

next()

print("Now I am going to pass it off to Victoria as we start breaking down the pyTLEX operations...")

next()

print("Let's start with examining how pyTLEX parses wall street journal 06")

next()

print("Here's a glimpse at the raw annotated text in the TimeML file")

next()

print("This data gets broken up into Events, Time Expressions, and Signals")
print("Which you can see here, this is the raw annotations from the previously shown text")
print("In an Event object, each must have an event id and a class, but some also have stems")
print("In Timex objects, each must have a tid, value, temporal function, phrase")
print("the optional variables in timex objects include type, mod, documentFunction, quantity, frequency, \n"
      "begin and end point")
print("Signals are the simplest objects, containing only a signal string and id")

next()

print("The files also contain Event Instances and Links, which we will capture")

next()

print("The parser discards unnecessary data, and builds a set of nodes and links which represents the graph")
print("Let's take a look at that output now...")

next()

print("Here is the set of nodes on the top, and set of links on the bottom")
print("You can take the time now to pause the video and compare these to the manually built photo of the graph on th"
      "e right")
print("You'll notice that there are 11 nodes and 13 links captured")
print("Each one of these IDs represent a node object, which can have values like part of speech or modality")
print("Note that no real analysis has been done so far, just collecting the data from the annotations")

next()

print("Now let's take a look at the partitioner")
print("It's job is to separate the graph based on it's subordinate links (which are shown as dashed arrows on the "
      "photo)")
# These represent...
# print("These links represent ")

next()

print("You can see the main partition, which is represented as the green nodes on the right")
print("And it's list of subordinate partitions, which are shown with their own colors")
print("Partition 1 relates to the set of red nodes on the right, and partition 2, 3, and 4 represent the singletons")

next()

print("So now Felipe will go into indeterminacy detector")
print("So let's take a look at the indeterminacy detector")
print("indeterminacies are defined as the instance where there's not enough information to uniquely specify the order")
print("which means that the order of these cannot be defined")

next()

print("As we can see for wall street journal 6, the indeterminacy score is 63.64%")
print("which means that the majority of time points in this timeline are indeterminate")
print("next we can see the indeterminate sections of the timeline, which we will touch on in the next "
      "section, are 1 - 5")
print("and lastly we are returned the complete set of indeterminate time points")
print("one thing to note here is that these nodes now have minus and plus postfixes")
print("which delineate the start and end of events or times respectively")

next()

print("now let's take a look at the culmination of TLEX, the extracted timelines, also known"
      " as the complete ordering of events and times")

next()

print("We can see the main timeline has 8 sections")
print("and from the previous slide, we can know that sections 1-5 are indeterminate")
print("The subordinate timelines deal with the subordinate partitions, we can see that timeline 0 "
      "relate to the nodes in red")
print("and because timelines 1 2 and 3 deal with singletons, they only contain the starts and ends of "
      "their respective nodes")

library(igraph)

# reading the network data from three separate files ---------------------------
# ignorying topics.csv for the time being
nodes  <- read.csv("data/nodes.csv",  sep = "\t", encoding = "UTF-8")
links  <- read.csv("data/links.csv",  sep = ",",  encoding = "UTF-8")
# topics <- read.csv("data/topics.csv", sep = "\t", encoding = "UTF-8")

# some dropping and renaming for convenience
names(nodes)[names(nodes)=="Page.ID"] <- "id"
names(nodes)[names(nodes)=="Name"]    <- "PageName"
names(links)[names(links)=="Source"]  <- "from"
names(links)[names(links)=="Target"]  <- "to"

# increasing all ID's by one as Pajek does not handle '0' for node id ----------
nodes$id   <- nodes$id + 1
links$from <- links$from + 1
links$to   <- links$to + 1

net <- graph_from_data_frame(d = links, vertices = nodes, directed = T)
# tyding our graph

write_graph(net, "wiki_norms.gml", format = "gml")

# saving in the Pajek format ---------------------------------------------------
# this is done in a manual way as write_graph does not work well
# write_graph(net, "wiki_norms.net", format = "pajek")

f_pajek_net <- file("wiki_norms.net", "w");

# dumping information about vertices
cat(sprintf("*vertices %d\n", length(V(net))), file = f_pajek_net)
for (i in 1:length(V(net))) {
  cat(sprintf("%d '%s'\n", i, V(net)$PageName[i]), file = f_pajek_net)
}

# dumping information about links
cat('*arcs\n', file = f_pajek_net)
net_links <- ends(net, E(net))
for (i in 1:length(E(net))) {
  cat(sprintf("%d %d\n", as.integer(net_links[i, 1]), as.integer(net_links[i, 2])), file = f_pajek_net)
}  

close(f_pajek_net)

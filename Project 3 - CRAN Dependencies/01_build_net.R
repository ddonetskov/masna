# It builds the network of dependencies between R packages.
#
#

# Configuration ----------------------------------------------------------------

rm(list = ls())                             # Remove all the objects we created so far.

library(igraph)
library(tools)

# Initilaization of major variables --------------------------------------------

# matrix of available packages, sadly it does not include the base ones (#BL)
pdb <- available.packages()
nrow_pdb <- nrow(pdb)

# vectors, they will be used later to build data frames to build the network
nodes_id   <- vector("integer")
nodes_name <- vector("character")
 
links_from <- vector("integer")
links_to   <- vector("integer")
links_type <- vector("character")

# hash table for looking up an index of package by the latter's name
nodes_ids <- new.env(hash = T)

# Populating the list of nodes -------------------------------------------------
for (i in 1:nrow_pdb) {
  pkg_name <- pdb[i,1]
  
  nodes_ids[[pkg_name]] <- i
  
  nodes_id[i]   <- i
  nodes_name[i] <- pkg_name
}

nodes <- data.frame(cbind(nodes_id, nodes_name))
names(nodes) <- c('id', 'name')

# Building the links -----------------------------------------------------------

link_seq = 0

for (i in 1:nrow_pdb) {

  pkg_name <- pdb[i,1]

  for (dep_type in c("Depends", "Imports", "Suggests", "Enhances")) {
    for (dep_pkg_name in package_dependencies(pkg_name, db = pdb, which = dep_type)[[1]]) {
      # using the hashed environment for the performance reason
      dep_pkg_name_id <- nodes_ids[[dep_pkg_name]]
      if (length(dep_pkg_name_id) > 0) {
        link_seq <- link_seq + 1
        links_from[link_seq] <- i
        links_to[link_seq]   <- dep_pkg_name_id
        links_type[link_seq] <- dep_type
      }
    }
    
  }
}

# ------------------------------------------------------------------------------
# this is a piece of old code which used the data frames but they are awful

# data frames for nodes and links
# nodes <- data.frame(matrix(NA, nrow = nrow(pdb), ncol = 2))
# names(nodes) <- c('id', 'name')
#
# links <- data.frame(matrix(NA, nrow = 10*nrow(pdb), ncol = 3))
# names(links) <- c('to', 'from', 'type')
#
# for (i in 1:nrow_pdb) {
#   nodes$id[i]   <- i
#   nodes$name[i] <- pkg_name
# }
#
# from the performnance point of view when we need to frequently change them
# for (dep_type in c("Depends", "Imports", "Suggests", "Enhances")) {
#   for (dep_pkg in package_dependencies(pdb[,1], db = pdb, which = dep_type)) {
#     # searching thorugh pdb with 'which' is a performance killer so we rather
#     # use the hashed environment
#     # getting the number (node_id) of dep_name
#     # dep_pkg_name_id <- which(pdb[,1] == dep_pkg_name)
#     dep_pkg_name    <- names(dep_pkg)
#     print(dep_pkg_name)
#     dep_pkg_name_id <- nodes_ids[[dep_pkg_name]]
#     if (length(dep_pkg_name_id) > 0) {
#       # print(which(pdb[,1] == dep_pkg_name))
#       link_seq <- link_seq + 1
#       links_from[link_seq] <- i
#       links_to[link_seq]   <- dep_pkg_name_id
#       links_type[link_seq] <- dep_type
#     }
#   }
# }
# ------------------------------------------------------------------------------

# Binding the information of links together
links <- data.frame(cbind(links_from, links_to, links_type))
names(links) <- c('to', 'from', 'type')

# Our network with all nodes
net <- graph_from_data_frame(d = links, vertices = nodes, directed = T)

# Export to gml ----------------------------------------------------------------
write_graph(net, "r_packages.gml", format = "gml")

# Export to Pajek --------------------------------------------------------------
# this is done in a manual way as write_graph does not work well
# write_graph(net, "r_packages.net", format = "pajek")

f_pajek_net <- file("r_packages.net", "w");

# dumping information about vertices
cat(sprintf("*vertices %d\n", length(V(net))), file = f_pajek_net)
for (i in 1:length(V(net))) {
  cat(sprintf("%d '%s'\n", i, V(net)$name[i]), file = f_pajek_net)
}

# dumping information about links
cat('*arcs\n', file = f_pajek_net)
net_links <- ends(net, E(net))
for (i in 1:length(E(net))) {
  # cat(sprintf("%d %d\n", 
  #             as.numeric(V(net)[net_links[i, 1]]),
  #             as.numeric(V(net)[net_links[i, 2]])), 
  #             file = f_pajek_net)
  # Unfortunately, have to revert to looking up in the hashed env nodes_ids
  # for the performance reasons
  cat(sprintf("%d %d\n",
              nodes_ids[[net_links[i, 1]]],        # the perf. trick
              nodes_ids[[net_links[i, 2]]]),       # the perf. trick
              file = f_pajek_net)
  
}  

close(f_pajek_net)

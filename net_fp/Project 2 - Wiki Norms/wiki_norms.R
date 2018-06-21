rm(list = ls())         # Remove all the objects we created so far.

library(igraph)

nodes  <- read.csv("heaberlin_dedeo_norm_network/nodes.csv",  sep = "\t", encoding = "UTF-8")
links  <- read.csv("heaberlin_dedeo_norm_network/links.csv",  sep = ",",  encoding = "UTF-8")
topics <- read.csv("heaberlin_dedeo_norm_network/topics.csv", sep = "\t", encoding = "UTF-8")

str(nodes)
str(links)
str(topics)

nrow(nodes); length(unique(nodes$id))
nrow(links); nrow(unique(links[, c("Source", "Target")]))

net <- graph_from_data_frame(d = links, vertices = nodes, directed = T)


pdf("wiki_norms.pdf")
plot(net, edge.arrow.size=.4)
dev.off()

# tkplot(net)

print(net, e = T, v = T)

1) It''s directed network'


determine basic network characteristics (directed/undirected; weights?; number of nodes, number of links, number of components; largest degree, diameter, acyclic?, …).
draw the degree (in directed also indegree and outdegree) distribution. List 20 nodes of largest degree.
determine the most important nodes.
determine some interesting subnetworks of your network and draw them. Interpret the results.




# net <- file("bib.net","w"); cat('*vertices ',n,'\n',file=net)
# clu <- file("bibMode.clu","w"); sex <- file("bibSex.clu","w")
# cat('%',file=clu); cat('%',file=sex)
# for(i in 1:length(mod)) cat(' ',i,mod[i],file=clu)
# cat('\n*vertices ',n,'\n',file=clu)
# for(i in 1:length(sx)) cat(' ',i,sx[i],file=sex)
# cat('\n*vertices ',n,'\n',file=sex)
# for(v in 1:n) {
#   cat(v,' "',nodes$name[v],'"\n',sep='',file=net);
#   cat(M[v],'\n',file=clu); cat(S[v],'\n',file=sex)
# }
# for(r in 1:length(rel)) cat('*arcs :',r,' "',rel[r],'"\n',sep='',file=net)
# cat('*arcs\n',file=net)
# for(a in 1:nrow(links))
#   cat(R[a],': ',F[a],' ',T[a],' 1 l "',rel[R[a]],'"\n',sep='',file=net)
# close(net); close(clu); close(sex)


# write_graph(net, "wiki_norms.net", format = "pajek")
write_graph(net, "wiki_norms.gml", format = "gml")




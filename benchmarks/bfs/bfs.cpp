/*
###############################################################################
# The code is adapted from one used in the CA course given by 
# Jason Lowe-Power's at UC Davis
# - https://github.com/jlpteaching/gem5-assignment3-wq25
###############################################################################
*/

#include <iostream>
#include <vector>

#include "graph.h"


#ifdef USEM5OPS
    #include <gem5/m5ops.h>
#endif

int main()
{
    std::vector<int> frontier;
    std::vector<int> next;

    frontier.clear();
    next.clear();

    frontier.push_back(0);

    std::cout << "Beginning BFS ..." << std::endl;

#ifdef USEM5OPS
    m5_reset_stats(0,0);
#endif

    while (!frontier.empty()) {
        for (auto vertex: frontier) {
            int start = columns[vertex];
            int end = columns[vertex + 1];
            for (int i = start; i < end; i++){
                int neighbor = edges[i];
                if (visited[neighbor] == 0) {
                    visited[neighbor] = 1;
                    next.push_back(neighbor);
                }
            }
        }
        frontier = next;
        next.clear();
    }

#ifdef USEM5OPS
    m5_dump_stats(0,0);
#endif

    std::cout << "Finished BFS." << std::endl;

    return 0;
}

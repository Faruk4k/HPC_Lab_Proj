from itertools import zip_longest
from m5.objects import SimpleNetwork, Switch, SimpleExtLink, SimpleIntLink


class LabSimplePt2Pt(SimpleNetwork):
    """A simple point-to-point network. This doesn't not use garnet."""

    def __init__(self, ruby_system, link_latency):
        super().__init__()
        self.netifs = []
        self._link_latency = link_latency

        # TODO: These should be in a base class
        # https://gem5.atlassian.net/browse/GEM5-1039
        self.ruby_system = ruby_system

    def connectControllers(self, controllers):
        """Connect all of the controllers to routers and connec the routers
        together in a point-to-point network.
        """
        # Create one router/switch per controller in the system
        self.routers = [Switch(router_id=i) for i in range(len(controllers))]

        # Make a link from each controller to the router. The link goes
        # externally to the network.
        self.ext_links = [
            SimpleExtLink(link_id=i, 
                          ext_node=c, 
                          int_node=self.routers[i]
                          )
            for i, c in enumerate(controllers)
        ]

        # Make an "internal" link (internal to the network) between every pair
        # of routers.
        link_count = 0
        int_links = []
        for ri in self.routers:
            for rj in self.routers:
                if ri == rj:
                    continue  # Don't connect a router to itself!
                link_count += 1
                int_links.append(
                    SimpleIntLink(link_id=link_count, 
                                  src_node=ri, 
                                  dst_node=rj,
                                  latency=self._link_latency,
                                  )
                )
        self.int_links = int_links


class LabL1L2ClusterTree(SimpleNetwork):
    """A simple tree network. This doesn't not use garnet.

    Assumptions:
      - The number of L1 controllers is the same as the number of L2
        controllers.
      - There is one directory

    Each L2 bank is paired with an L1 controller. The order of the controllers
    in the two lists determines the pairing.
    The L2s are connected to a single router (crossbar).
    The directory is then also connected to this router.
    """

    _intLinkId = 0
    _extLinkId = 0
    _routerId = 0

    @classmethod
    def _getIntLinkId(cls):
        cls._intLinkId += 1
        return cls._intLinkId - 1

    @classmethod
    def _getExtLinkId(cls):
        cls._extLinkId += 1
        return cls._extLinkId - 1

    @classmethod
    def _getRouterId(cls):
        cls._routerId += 1
        return cls._routerId - 1

    def __init__(self, ruby_system, link_latency):
        super().__init__()
        self.netifs = []
        self._link_latency = link_latency

        # TODO: These should be in a base class
        # https://gem5.atlassian.net/browse/GEM5-1039
        self.ruby_system = ruby_system

    def connectControllers(self, l1_ctrls, l2_ctrls, dir_ctrl):
        """Connect all of the controllers to routers and connect the routers
        together as specified in the docstring of the class.
        Assumptions:
        - The number of L1 controllers is the same as the number of L2
            controllers.
        - There is one directory
        """
        # NOTE: Hack for SE mode with a `- 1` here and the first two L1s
        # are connected to a single L2
        assert len(l1_ctrls) - 1 == len(l2_ctrls)

        routers = []
        int_links = []
        ext_links = []

        self.xbar = Switch(router_id=self._getRouterId())
        routers.append(self.xbar)

        # for every l1/l2 pair create a connection. Then, connect this to a
        # xbar.
        for i, (l1, l2) in enumerate(zip(l1_ctrls[1:], l2_ctrls)):
            # Create the router/switch
            l1_switch = Switch(router_id=self._getRouterId())
            setattr(self, f"l1_switch_{i}", l1_switch)
            routers.append(getattr(self, f"l1_switch_{i}"))
            # Connect the l1
            setattr(
                self,
                f"l1_link_{i}",
                SimpleExtLink(
                    link_id=self._getExtLinkId(),
                    ext_node=l1,
                    int_node=l1_switch,
                ),
            )
            ext_links.append(getattr(self, f"l1_link_{i}"))

            # Add router for L2
            l2_switch = Switch(router_id=self._getRouterId())
            setattr(self, f"l2_switch_{i}", l2_switch)
            routers.append(getattr(self, f"l2_switch_{i}"))
            # Connect the L2
            setattr(
                self,
                f"l2_link_{i}",
                SimpleExtLink(
                    link_id=self._getExtLinkId(),
                    ext_node=l2,
                    int_node=l2_switch,
                ),
            )
            ext_links.append(getattr(self, f"l2_link_{i}"))

            # Connect L1 router to L2 router
            setattr(
                self,
                f"l1_l2_link{i}",
                SimpleIntLink(
                    link_id=self._getIntLinkId(),
                    src_node=l1_switch,
                    dst_node=l2_switch,
                ),
            )
            int_links.append(getattr(self, f"l1_l2_link{i}"))
            setattr(
                self,
                f"l2_l1_link{i}",
                SimpleIntLink(
                    link_id=self._getIntLinkId(),
                    src_node=l2_switch,
                    dst_node=l1_switch,
                ),
            )
            int_links.append(getattr(self, f"l2_l1_link{i}"))

            # Connect the L2 router to the xbar
            setattr(
                self,
                f"l2_xbar_link{i}",
                SimpleIntLink(
                    link_id=self._getIntLinkId(),
                    src_node=l2_switch,
                    dst_node=self.xbar,
                    latency=self._link_latency,
                ),
            )
            int_links.append(getattr(self, f"l2_xbar_link{i}"))
            setattr(
                self,
                f"xbar_l2_link{i}",
                SimpleIntLink(
                    link_id=self._getIntLinkId(),
                    src_node=self.xbar,
                    dst_node=l2_switch,
                    latency=self._link_latency,
                ),
            )
            int_links.append(getattr(self, f"xbar_l2_link{i}"))

        # Connect the directory to the xbar
        self.dir_ext_link = SimpleExtLink(
            link_id=self._getExtLinkId(), ext_node=dir_ctrl, int_node=self.xbar
        )
        ext_links.append(self.dir_ext_link)

        # HACK: Connect first L1 directory to the xbar
        self.hack_ext_link = SimpleExtLink(
            link_id=self._getExtLinkId(),
            ext_node=l1_ctrls[0],
            int_node=self.xbar,
        )
        ext_links.append(self.hack_ext_link)

        self.ext_links = ext_links
        self.int_links = int_links
        self.routers = routers


from m5.params import *
from m5.objects import *

from m5.objects import GarnetNetwork, GarnetExtLink, GarnetIntLink, GarnetRouter, GarnetNetworkInterface

# Creates a generic Mesh assuming an equal number of cache
# and directory controllers.
# XY routing is enforced (using link weights)
# to guarantee deadlock freedom.

class LabGarnetPt2Pt(GarnetNetwork):
    """A point-to-point network using garnet.
    """

    def __init__(self, ruby_system, link_latency):
        super().__init__()


        self.ruby_system = ruby_system
        self._link_latency = link_latency

    def connectControllers(self, controllers):
        # Create one router/switch per controller in the system
        self.routers = [
            GarnetRouter(router_id = i) for i in range(len(controllers))
        ]
        self.ext_links = [GarnetExtLink(link_id=i, ext_node=c,
                                        int_node=self.routers[i],
                                        latency = self._link_latency)
                          for i, c in enumerate(controllers)]

        self.netifs = [GarnetNetworkInterface(id=i) \
                    for (i,n) in enumerate(self.ext_links)]

        link_count = 0
        self.int_links = []
        for ri in (self.routers):
            for rj in (self.routers):
                if ri == rj: continue # Don't connect a router to itself!
                link_count += 1
                self.int_links.append(GarnetIntLink(link_id = link_count,
                                                    src_node = ri,
                                                    dst_node = rj,
                                                    latency = self._link_latency,
                                                    weight  = 1))
                
class LabGarnetMesh(GarnetNetwork):

    def __init__(self, ruby_system, link_latency):
        super().__init__()
        self.ruby_system = ruby_system
        self._link_latency = link_latency
        self._router_latency = 5

    # Makes a generic mesh
    # assuming an equal number of cache and directory cntrls

    def connectControllers(self, controllers, ncpu):
        num_routers = ncpu
        num_rows = 2
        nodes = controllers

        # default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        #link_latency = 8
        #router_latency = 3


        # There must be an evenly divisible number of controllers to routers
        # Also, obviously the number or rows must be <= the number of routers
        cntrls_per_router, remainder = divmod(len(nodes), num_routers)
        assert(num_rows > 0 and num_rows <= num_routers)
        num_columns = int(num_routers / num_rows)
        assert(num_columns * num_rows == num_routers)
        # Create the routers in the mesh
        self.routers = [GarnetRouter(router_id=i, latency = self._router_latency) \
            for i in range(num_routers)]

        # link counter to set unique link ids
        link_count = 0

        # Add all but the remainder nodes to the list of nodes to be uniformly
        # distributed across the network.
        network_nodes = []
        remainder_nodes = []
        for node_index in range(len(nodes)):
            if node_index < (len(nodes) - remainder):
                network_nodes.append(nodes[node_index])
            else:
                remainder_nodes.append(nodes[node_index])

        # Connect each node to the appropriate router
        ext_links = []
        for (i, n) in enumerate(network_nodes):
            cntrl_level, router_id = divmod(i, num_routers)
            assert(cntrl_level < cntrls_per_router)
            ext_links.append(GarnetExtLink(link_id=link_count, ext_node=n,
                                    int_node=self.routers[router_id],
                                    latency = self._link_latency))
            link_count += 1

        # Connect the remaining nodes to router 0.  These should only be
        # DMA nodes.
        for (i, node) in enumerate(remainder_nodes):
            assert(i < remainder)
            ext_links.append(GarnetExtLink(link_id=link_count, ext_node=node,
                                    int_node=self.routers[0],
                                    latency = self._link_latency))
            link_count += 1

        self.ext_links = ext_links

        self.netifs = [GarnetNetworkInterface(id=i) \
                    for (i,n) in enumerate(self.ext_links)]

        # Create the mesh links.
        int_links = []

        # East output to West input links (weight = 1)
        for row in range(num_rows):
            for col in range(num_columns):
                if (col + 1 < num_columns):
                    east_out = col + (row * num_columns)
                    west_in = (col + 1) + (row * num_columns)
                    int_links.append(GarnetIntLink(link_id=link_count,
                                             src_node=self.routers[east_out],
                                             dst_node=self.routers[west_in],
                                             src_outport="East",
                                             dst_inport="West",
                                             latency = self._link_latency,
                                             weight=1))
                    link_count += 1

        # West output to East input links (weight = 1)
        for row in range(num_rows):
            for col in range(num_columns):
                if (col + 1 < num_columns):
                    east_in = col + (row * num_columns)
                    west_out = (col + 1) + (row * num_columns)
                    int_links.append(GarnetIntLink(link_id=link_count,
                                             src_node=self.routers[west_out],
                                             dst_node=self.routers[east_in],
                                             src_outport="West",
                                             dst_inport="East",
                                             latency = self._link_latency,
                                             weight=1))
                    link_count += 1

        # North output to South input links (weight = 2)
        for col in range(num_columns):
            for row in range(num_rows):
                if (row + 1 < num_rows):
                    north_out = col + (row * num_columns)
                    south_in = col + ((row + 1) * num_columns)
                    int_links.append(GarnetIntLink(link_id=link_count,
                                             src_node=self.routers[north_out],
                                             dst_node=self.routers[south_in],
                                             src_outport="North",
                                             dst_inport="South",
                                             latency = self._link_latency,
                                             weight=2))
                    link_count += 1

        # South output to North input links (weight = 2)
        for col in range(num_columns):
            for row in range(num_rows):
                if (row + 1 < num_rows):
                    north_in = col + (row * num_columns)
                    south_out = col + ((row + 1) * num_columns)
                    int_links.append(GarnetIntLink(link_id=link_count,
                                             src_node=self.routers[south_out],
                                             dst_node=self.routers[north_in],
                                             src_outport="South",
                                             dst_inport="North",
                                             latency = self._link_latency,
                                             weight=2))
                    link_count += 1


        self.int_links = int_links

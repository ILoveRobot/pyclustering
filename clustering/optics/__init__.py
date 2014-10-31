from support import euclidean_distance;


class optics_descriptor:
    reachability_distance = None;
    core_distance = None;
    
    processed = None;
    index_object = None;
    
    def __init__(self, index, core_distance = None, reachability_distance = None):
        self.index_object = index;
        self.core_distance = core_distance;
        self.reachability_distance = reachability_distance;
        self.processed = False;
        
    def __repr__(self):
        return '(%s, [c: %s, r: %s])' % (self.index_object, self.core_distance, self.reachability_distance);
    

class optics:
    __optics_objects = None;      # List of OPTICS objects that corresponds to objects from input sample.
    __ordered_database = None;    # List of OPTICS objects in traverse order. 
    
    __clusters = None;            # Result of clustering (list of clusters where each cluster contains indexes of objects from input data).
    __noise = None;               # Result of clustering (noise).
    
    __sample_pointer = None;      # Algorithm parameter - pointer to sample for processing.
    __eps = 0;                    # Algorithm parameter - connectivity radius between object for establish links between object.
    __minpts = 0;                 # Algorithm parameter - minimum number of neighbors that is required for establish links between object.
    
    __ccore_algorithm_pointer = None;
    
    def __init__(self, sample, eps, minpts):
        "Constructor of clustering algorithm OPTICS."
        
        "(in) sample      - input data that is presented as list of points (objects), each point should be represented by list or tuple."
        "(in) eps         - connectivity radius between points, points may be connected if distance between them less then the radius."
        "(in) minpts      - minimum number of shared neighbors that is required for establish links between points."
         
        self.__processed = [False] * len(sample);
        self.__optics_objects = [optics_descriptor(i) for i in range(len(sample))];
        self.__ordered_database = [];
        
        self.__sample_pointer = sample;
        self.__eps = eps;
        self.__minpts = minpts;


    def process(self):
        "Performs cluster analysis in line with rules of OPTICS algorithm. Results of clustering can be obtained using corresponding gets methods."  
        
        for optic_object in self.__optics_objects:
            if (optic_object.processed is False):
                self.__expand_cluster_order(optic_object);
        
        self.__extract_clusters();
    
    
    def get_clusters(self):
        "Returns list of allocated clusters, each cluster contains indexes of objects in list of data."
        
        return self.__clusters;
    
    
    def get_noise(self):
        "Returns list of noise that contains indexes of objects that corresponds to input data."
        return self.__noise;
    
    
    def get_cluster_ordering(self):
        "Returns clustering ordering that uses reachability distances."  
        ordering = [ optics_object.reachability_distance for optics_object in self.__optics_objects if optics_object.reachability_distance is not None ];
        return ordering;
    
    
    def __expand_cluster_order(self, optics_object):
        "Expand cluster order from not processed optic-object that corresponds to object from input data."
        "Traverse procedure is performed until objects are reachable from core-objects in line with connectivity radius."
        "Order database is updated during expanding."
    
        "(in) optics_object   - object that hasn't been processed."
        
        optics_object.processed = True;
        
        neighbors_descriptor = self.__neighbor_indexes(optics_object);
        optics_object.reachability_distance = None;
        
        self.__ordered_database.append(optics_object);
        
        # Check core distance
        if (len(neighbors_descriptor) >= self.__minpts):
            neighbors_descriptor.sort(key = lambda obj: obj[1]); # TODO: Find three smallest distances much faster than sorting
            optics_object.core_distance = neighbors_descriptor[self.__minpts - 1][1];
            
            # Continue processing
            order_seed = list();
            self.__update_order_seed(optics_object, neighbors_descriptor, order_seed);
            
            while(len(order_seed) > 0):
                optic_descriptor = order_seed[0];
                order_seed.remove(optic_descriptor);
                
                neighbors_descriptor = self.__neighbor_indexes(optic_descriptor);
                optic_descriptor.processed = True;
                
                self.__ordered_database.append(optic_descriptor);
                
                if (len(neighbors_descriptor) >= self.__minpts):
                    neighbors_descriptor.sort(key = lambda obj: obj[1]);    # TODO: Find three smallest distances much faster than sorting
                    optic_descriptor.core_distance = neighbors_descriptor[self.__minpts - 1][1];
                    
                    self.__update_order_seed(optic_descriptor, neighbors_descriptor, order_seed);
                else:
                    optic_descriptor.core_distance = None;
                    
        else:
            optics_object.core_distance = None;

    
    def __extract_clusters(self):
        "Extract clusters and noise from order database."
     
        self.__clusters = [];
        self.__noise = [];

        current_cluster = [];
        for optics_object in self.__ordered_database:
            if ((optics_object.reachability_distance is None) or (optics_object.reachability_distance > self.__eps)):
                if ((optics_object.core_distance is not None) and (optics_object.core_distance <= self.__eps)):
                    if (len(current_cluster) > 0):
                        self.__clusters.append(current_cluster);
                        current_cluster = [];
                        
                    current_cluster.append(optics_object.index_object);
                else:
                    self.__noise.append(optics_object.index_object);
            else:
                current_cluster.append(optics_object.index_object);
        
        if (len(current_cluster) > 0):
            self.__clusters.append(current_cluster);
                

    def __update_order_seed(self, optic_descriptor, neighbors_descriptor, order_seed):
        "Update sorted list of reachable objects (from core-object) that should be processed using neighbors of core-object."
        
        "(in) optic_descriptor         - core-object whose neighbors should be analysed."
        "(in) neighbors_descriptor     - list of neighbors of core-object."
        "(in/out) order_seed           - pointer to list of sorted object in line with reachable distance."

        for neighbor_descriptor in neighbors_descriptor:
            index_neighbor = neighbor_descriptor[0];
            current_reachable_distance = neighbor_descriptor[1];
            
            if (self.__optics_objects[index_neighbor].processed != True):
                reachable_distance = max(current_reachable_distance, optic_descriptor.core_distance);
                if (self.__optics_objects[index_neighbor].reachability_distance is None):
                    self.__optics_objects[index_neighbor].reachability_distance = reachable_distance;
                    
                    order_seed.append(self.__optics_objects[index_neighbor]);
                    order_seed.sort(key = lambda obj: obj.reachability_distance); # TODO: Rellocation is less complexity than sorting
                else:
                    if (reachable_distance < self.__optics_objects[index_neighbor].reachability_distance):
                        self.__optics_objects[index_neighbor].reachability_distance = reachable_distance;
                        
                        order_seed.sort(key = lambda obj: obj.reachability_distance); # TODO: Rellocation is less complexity than sorting


    def __neighbor_indexes(self, optic_object):  
        "Private function that is used by dbscan. Return list of indexes of neighbors of specified point for the data."
    
        "(in) optic_object     - object for which neighbors should be returned in line with connectivity radius."
        
        "Return list of indexes of neighbors in line the connectivity radius."
              
        neighbor_description = [];
        
        for index in range(0, len(self.__sample_pointer), 1):
            if (index == optic_object.index_object):
                continue;
            
            distance = euclidean_distance(self.__sample_pointer[optic_object.index_object], self.__sample_pointer[index]);
            if (distance <= self.__eps):
                neighbor_description.append( [index, distance] );
            
        return neighbor_description;
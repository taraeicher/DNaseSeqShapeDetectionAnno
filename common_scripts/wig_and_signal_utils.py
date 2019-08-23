import numpy as np
import math
import sys

"""
Estimate the number of crests in the region.
Do this by checking the number of trough-crest-trough triples,
where trough and crest are signals within a threshold of the
max and min.
""" 
def find_crossing_count(region, threshold):
               
    is_below = True
    crossing_count = 0

    for sig in np.nditer(region):
        #If the last thing we saw was a trough and we found a crest, update the last thing
        #we saw to a crest.
        if is_below and sig >= threshold:
            is_below = False

        #If the last thing we saw was a crest and we found a trough, update the last thing
        #we saw to a trough and update the crest count.
        if (not is_below) and sig < threshold:
            is_below = True
            crossing_count += 1

    #If we did not find a trough-crest-trough combo, set number of crests to the fraction of the threshold.
    if crossing_count == 0:
        crossing_count = min(1, np.max(region) / threshold)
        
    return crossing_count
        
"""
Returns the Xth percentile of intensity for all records in the file. 
NOTE: 1000000 is the highest possible RPKM intensity.
"""
def get_intensity_percentile(percentile, file):
   
    fine_bin_count = 4
    max_threshold = 1000000 * fine_bin_count
    counts = np.zeros(max_threshold)        
    file_line_count = 0
    
    #Use each entry in the file to calculate running metadata.
    next_line = file.readline()
    
    while next_line:
        split_line = next_line.split()
        if len(split_line) == 4:
            val = float(split_line[3]) * fine_bin_count

            #Increment the count of lines in the file.
            file_line_count += 1
            
            #Get the maximum value and increment the appropriate location in the array.
            bin = int(math.ceil(val))
            counts[bin] += 1
            
            #Let the user know we are still processing.
            if file_line_count % 10000 == 0:
                sys.stdout.write('.')
                
        #Read the next line.
        next_line = file.readline()

    #Find percentile of maxes.
    target_count = int(file_line_count * percentile)
    running_sum = 0
    i = 0
    percentile_found = False
    max_sig_percentile = 0
    
    while i < len(counts) - 1 and not percentile_found:
        running_sum += counts[i]
        if running_sum >= target_count:
            max_sig_percentile = i
            percentile_found = True
        i += 1
    i = 0
    percentile_found = False
    running_sum = 0
        
    #Rewind file and return values.
    file.seek(0)
    retval = max_sig_percentile / fine_bin_count
    return retval
    
#Get the cross-correlation metric between the two clusters.
def get_crosscorr(clust1, clust2, delay, threshold, max_cutoff, use_max_cutoff, two_way, minimum):
    
    #Get the section of the cluster that does not include the delay.
    clust1_array = np.asarray(clust1)
    clust2_array = np.asarray(clust2)

    #If the clusters are the same length, use subarrays to simulate the shift.
    #Otherwise, move the smaller array across the larger one.
    if two_way:
        if delay < 0:
            #Simulate the shift by moving the second cluster to the right.
            clust1_array = np.asarray(clust1[0:(len(clust1) + delay)])
            clust2_array = np.asarray(clust2[abs(delay):len(clust2)])
            
        else:
            #Simulate the shift by moving the first cluster to the right.
            clust2_array = np.asarray(clust2[0:(len(clust2) - delay)])
            clust1_array = np.asarray(clust1[delay:len(clust1)])
    elif len(clust1_array) > len(clust2_array):
        if delay < 0:
            raise ValueError("Cannot use a negative delay")
            
        else:
            clust1_array = np.asarray(clust1[delay:(len(clust2) + delay)])
    else:
        if delay < 0:
            raise ValueError("Cannot use a negative delay")
            
        else:
            clust2_array = np.asarray(clust2[delay:(len(clust1) + delay)])
    
    #Only calculate the cross-correlation if the sub-regions of both clusters contain the max
    #and the maximums are within the threshold.
    #Else, throw an error.
    both_contain_max = np.max(np.asarray(clust1)) == np.max(clust1_array) and np.max(np.asarray(clust2)) == np.max(clust2_array)
    max_of_two = max(np.max(np.asarray(clust1)), np.max(np.asarray(clust2)))
    min_of_two = min(np.max(np.asarray(clust1)), np.max(np.asarray(clust2)))
    maxes_within_threshold =  min_of_two / max_of_two > threshold or max_of_two == minimum

    if max_of_two < max_cutoff and use_max_cutoff:
        return 1
    elif both_contain_max and maxes_within_threshold:
        #Calculate the cross-correlation pieces.    
        numerator = np.sum(clust1_array * clust2_array) - np.sum(clust1_array) * np.sum(clust2_array) / len(clust2_array)
        denominator_1 = np.sum(np.square(clust1_array)) - np.square(np.sum(clust1_array)) / len(clust1_array)
        denominator_2 = np.sum(np.square(clust2_array)) - np.square(np.sum(clust2_array)) / len(clust2_array)
        denominator = 1
        if denominator_1 > 0 and denominator_2 > 0:
            denominator = np.sqrt(denominator_1 * denominator_2)
        else:
            numerator = 0
    else:
        raise ValueError("Maximum signal intensity not contained in region")
        
    #Return the cross-correlation result.
    return numerator / denominator
    
#Count signals above a value.
def count_above(threshold, annotation, signal, start, end, start_anno, end_anno, bin_sz):
    count = 0
    start_idx = start
    for sig in signal:
        is_between_anno = (start_anno <= start_idx) and (start_idx <= end_anno)
        if sig > threshold and (is_between_anno or annotation == ""):
            count += bin_sz
        start_idx += bin_sz
    return count
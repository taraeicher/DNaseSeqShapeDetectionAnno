#PBS -l nodes=1:ppn=28
#PBS -l walltime=2:00:00 
#!/bin/bash   
# """
# Dependencies:
# 1. Tensorflow, which can be installed here: https://www.tensorflow.org/install/install_linux
# 2. Samtools: https://sourceforge.net/projects/samtools/files/
# 3. Taolib directory: https://github.com/taoliu/taolib
# 4. Gap statistic code: https://github.com/minddrummer/gap
# 5. Added to your path: gap
# 6. Bedtools
# 7. Kent utilities
# 8. Bamtools
# 9. BamCoverage

#Variables
    USAGE="This script is used for creating training regions from an input WIG file for each chromosome. It splits the WIG file into regions of a specified size with a specified overlap margin and a specified factor for the linear decrease in weights from the center of the region. In this script, a grid of factors and overlap margins are tested, and the optimal pair of parameters is reported.\n
    The following parameters are optional, but recommended:\n
    <-n> The name of the cell line (e.g. Brain)\n
    <-d> The base filename where the input and output files will be stored (e.g. '/root/annoshaperun/').\n
    <-i> The bin size used to generate the WIG file (default: 50 bp)\n
    <-r> The region size used for splitting (default: 4 kbp)"
    
    CELL_LINE=""
    REGION_SIZE=4000
    BASE_FILENAME=""
    CHROMS_NUM="1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22"
    BIN_SIZE=50
    BLACKLIST=""
    while getopts n:d:i:r: option; do
        case "${option}" in
            n) CELL_LINE=$OPTARG;;
            d) BASE_FILENAME=$(realpath $OPTARG);;
            i) BIN_SIZE=$OPTARG;;
            r) REGION_SIZE=$OPTARG;;
        esac
    done
    BASE_PATH=$BASE_FILENAME/$CELL_LINE
    
#Print message to user.
    echo -e $USAGE
    echo "Creating regions using the following settings:"
    echo "Name is $CELL_LINE"
    echo "Base directory is $BASE_FILENAME"
    echo "Bin size in WIG file is $BIN_SIZE"
    echo "Region size for annotation is $REGION_SIZE"
    echo -e "-------------------------------------------------------------------------------------------------------------------------\n"
	
#Create all needed directories.
    TRAINING_FILES="$BASE_PATH/training"
    if [[ ! -e $TRAINING_FILES ]]; then
        mkdir $TRAINING_FILES
    fi

    #Generate input files for training and annotation. NOTE: Don't double the size for files to annotate. Keep the same margins, but overlap.
    if [[ ! -e $TRAINING_FILES/percentile_cutoffs/ ]]; then
        mkdir $TRAINING_FILES/percentile_cutoffs/
    fi
    
    split_and_shift() {
        factor=$1
        margin=$2
        if [[ ! -e $TRAINING_FILES/${factor}_${margin}/ ]]; then
                mkdir $TRAINING_FILES/${factor}_${margin}/
            fi
        if [[ ! -e $TRAINING_FILES/${factor}_${margin}_shifted/ ]]; then
            mkdir $TRAINING_FILES/${factor}_${margin}_shifted/
        fi
        if [[ ! -e $TRAINING_FILES/${factor}_${margin}_crossings/ ]]; then
            mkdir $TRAINING_FILES/${factor}_${margin}_crossings/
        fi
        for c in $CHROMS_NUM;
        do
            python ../common_scripts/split_regions.py ${BASE_PATH}/wig/$c.wig $BIN_SIZE $c $TRAINING_FILES/${factor}_${margin}/chrom${c}.pkl $REGION_SIZE $margin $factor 0.95 $TRAINING_FILES/${factor}_${margin}_shifted/chrom${c}.pkl $TRAINING_FILES/${factor}_${margin}_crossings/chrom${c}.txt $TRAINING_FILES/percentile_cutoffs/chrom${c}.txt
            
            echo "Splitting complete for chromosome $c with factor $factor and margin $margin"

        done    
    }
    
    pids=""
    for fac in 0.1 0.2 0.3 0.4 0.5
    do
        for marg in 0 $(python -c "print($REGION_SIZE*0.1)") $(python -c "print($REGION_SIZE*0.2)") $(python -c "print($REGION_SIZE*0.3)") $(python -c "print($REGION_SIZE*0.4)") $(python -c "print($REGION_SIZE*0.5)")
        do
            split_and_shift $fac $marg &
            pids="$pids $!"
        done
    done
    wait $pids
    echo "All splitting complete!"
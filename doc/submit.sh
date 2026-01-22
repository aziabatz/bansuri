#!/bin/bash
#SBATCH --job-name=hot_reload_manager
#SBATCH --output=master_%j.log
#SBATCH --error=master_%j.err
#SBATCH --time=7-00:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G
#SBATCH --partition=standard

# Hot-Reload Script Manager SLURM Job
# This script runs continuously and manages child scripts based on JSON config

echo "=========================================="
echo "Hot-Reload Script Manager"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Started at: $(date)"
echo "=========================================="

# Load any required modules (modify as needed)
# module load python/3.9

# Run the master script
python master.py

echo "=========================================="
echo "Job finished at: $(date)"
echo "=========================================="

#!/usr/bin/env python3
"""
Simple API for monitoring the ETL pipeline
"""

import os
import json
import glob
from flask import Flask, jsonify
from dotenv import load_dotenv
from etl_pipeline import ETLPipeline

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize ETL pipeline
etl_pipeline = ETLPipeline()

# Establish connections
etl_pipeline.connect_to_data_warehouse()
etl_pipeline.connect_to_sources()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    is_healthy, message = etl_pipeline.health_check()
    status = 200 if is_healthy else 500
    return jsonify({
        'status': 'healthy' if is_healthy else 'unhealthy',
        'message': message
    }), status

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get ETL run statistics"""
    stats = etl_pipeline.get_run_stats()
    return jsonify(stats)

@app.route('/quality-reports', methods=['GET'])
def get_latest_quality_report():
    """Get the latest data quality report"""
    try:
        # Find the latest quality report file
        report_files = glob.glob('/app/logs/quality_report_*.json')
        if not report_files:
            return jsonify({'error': 'No quality reports found'}), 404
            
        # Sort by timestamp and get the latest
        latest_report = sorted(report_files, reverse=True)[0]
        
        # Read and return the report
        with open(latest_report, 'r') as f:
            report = json.load(f)
            
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/trigger', methods=['POST'])
def trigger_etl():
    """Trigger a full ETL run"""
    try:
        etl_pipeline.run_full_etl()
        return jsonify({'status': 'success', 'message': 'ETL process started'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/quality-reports/all', methods=['GET'])
def get_all_quality_reports():
    """Get all data quality reports"""
    try:
        # Find all quality report files
        report_files = glob.glob('/app/logs/quality_report_*.json')
        if not report_files:
            return jsonify({'reports': []})
            
        # Sort by timestamp
        report_files = sorted(report_files, reverse=True)
        
        # Limit to last 10 reports
        report_files = report_files[:10]
        
        reports = []
        for report_file in report_files:
            with open(report_file, 'r') as f:
                report = json.load(f)
                reports.append({
                    'filename': os.path.basename(report_file),
                    'report': report
                })
            
        return jsonify({'reports': reports})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
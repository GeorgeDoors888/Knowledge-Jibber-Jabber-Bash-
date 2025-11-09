#!/usr/bin/env python3
"""
Duplicate Management Utility
Standalone tool for finding, analyzing, and managing duplicates
across multiple Google Sheets.
"""

import argparse
import sys
import os
from datetime import datetime
import json

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_sheet_manager import MultiSheetManager
from duplicate_detector import DuplicateDetector, DuplicateManager
from config import DRIVE_FOLDER_ID, DUPLICATE_CHECK_FIELDS, DUPLICATE_DETECTION_METHOD


def scan_for_duplicates(folder_id=None, output_file=None, method=None):
    """Scan all spreadsheets for duplicates and generate report"""
    print("🔍 Starting duplicate scan...")
    
    manager = MultiSheetManager(folder_id=folder_id)
    
    if method:
        manager.configure_duplicate_detection(method=method)
    
    report = manager.find_all_duplicates(save_report=True)
    
    if report:
        print(f"\n📊 DUPLICATE SCAN RESULTS:")
        print(f"   Total duplicates found: {report['summary']['total_duplicates']}")
        print(f"   Sheets affected: {report['summary']['sheets_affected']}")
        print(f"   Match types: {report['summary']['match_types']}")
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"   Report saved to: {output_file}")
        
        return report
    else:
        print("❌ Failed to generate duplicate report")
        return None


def clean_duplicates(folder_id=None, strategy="keep_first", dry_run=True):
    """Clean up duplicates using specified strategy"""
    print(f"🧹 Starting duplicate cleanup (strategy: {strategy}, dry_run: {dry_run})...")
    
    manager = MultiSheetManager(folder_id=folder_id)
    result = manager.remove_duplicates(strategy=strategy, dry_run=dry_run)
    
    if result:
        print(f"\n🧹 CLEANUP RESULTS:")
        print(f"   Duplicates found: {result['total_duplicates_found']}")
        print(f"   Removal attempted: {result['removal_attempted']}")
        print(f"   Successful: {result['removal_successful']}")
        print(f"   Failed: {result['removal_failed']}")
    
    return result


def analyze_duplicate_patterns(folder_id=None):
    """Analyze patterns in duplicate data"""
    print("📈 Analyzing duplicate patterns...")
    
    manager = MultiSheetManager(folder_id=folder_id)
    report = manager.find_all_duplicates(save_report=False)
    
    if not report or not report['duplicates']:
        print("✅ No duplicates found to analyze")
        return
    
    # Analyze patterns
    patterns = {
        'match_types': {},
        'field_patterns': {},
        'sheet_patterns': {},
        'similarity_scores': []
    }
    
    for dup in report['duplicates']:
        # Match type analysis
        match_type = dup['match_info']['match_type']
        patterns['match_types'][match_type] = patterns['match_types'].get(match_type, 0) + 1
        
        # Similarity score analysis
        score = dup['match_info'].get('match_score', 0)
        patterns['similarity_scores'].append(score)
        
        # Sheet pattern analysis
        sheet1 = dup.get('sheet_1', 'Unknown')
        sheet2 = dup.get('sheet_2', 'Unknown')
        if sheet1 == sheet2:
            patterns['sheet_patterns']['within_sheet'] = patterns['sheet_patterns'].get('within_sheet', 0) + 1
        else:
            patterns['sheet_patterns']['cross_sheet'] = patterns['sheet_patterns'].get('cross_sheet', 0) + 1
    
    # Calculate statistics
    if patterns['similarity_scores']:
        avg_score = sum(patterns['similarity_scores']) / len(patterns['similarity_scores'])
        min_score = min(patterns['similarity_scores'])
        max_score = max(patterns['similarity_scores'])
    else:
        avg_score = min_score = max_score = 0
    
    print(f"\n📈 DUPLICATE PATTERN ANALYSIS:")
    print(f"   Total duplicates analyzed: {len(report['duplicates'])}")
    print(f"   Match types: {patterns['match_types']}")
    print(f"   Sheet distribution: {patterns['sheet_patterns']}")
    print(f"   Similarity scores - Avg: {avg_score:.1f}%, Min: {min_score}%, Max: {max_score}%")
    
    return patterns


def interactive_duplicate_review(folder_id=None):
    """Interactive review of duplicates"""
    print("🔍 Starting interactive duplicate review...")
    
    manager = MultiSheetManager(folder_id=folder_id)
    report = manager.find_all_duplicates(save_report=False)
    
    if not report or not report['duplicates']:
        print("✅ No duplicates found for review")
        return
    
    print(f"Found {len(report['duplicates'])} duplicate pairs to review")
    
    actions_taken = {
        'kept_original': 0,
        'kept_duplicate': 0,
        'skipped': 0,
        'flagged': 0
    }
    
    for i, dup in enumerate(report['duplicates'], 1):
        print(f"\n--- Duplicate {i}/{len(report['duplicates'])} ---")
        print(f"Match Type: {dup['match_info']['match_type']}")
        print(f"Match Score: {dup['match_info']['match_score']}%")
        print(f"Sheets: {dup.get('sheet_1', 'Unknown')} vs {dup.get('sheet_2', 'Unknown')}")
        
        print("\nOriginal Record:")
        for key, value in dup['original_row'].items():
            if key in DUPLICATE_CHECK_FIELDS:
                print(f"  * {key}: {value}")
            else:
                print(f"    {key}: {value}")
        
        print("\nDuplicate Record:")
        for key, value in dup['duplicate_row'].items():
            if key in DUPLICATE_CHECK_FIELDS:
                print(f"  * {key}: {value}")
            else:
                print(f"    {key}: {value}")
        
        while True:
            choice = input("\nAction: (k)eep original, (d)elete duplicate, (s)kip, (f)lag both, (q)uit: ").lower()
            
            if choice == 'k':
                actions_taken['kept_original'] += 1
                print("✓ Keeping original record")
                break
            elif choice == 'd':
                actions_taken['kept_duplicate'] += 1
                print("✓ Marked duplicate for deletion")
                break
            elif choice == 's':
                actions_taken['skipped'] += 1
                print("⏭ Skipped")
                break
            elif choice == 'f':
                actions_taken['flagged'] += 1
                print("🚩 Flagged both records")
                break
            elif choice == 'q':
                print("👋 Exiting interactive review")
                break
            else:
                print("❌ Invalid choice. Please use k, d, s, f, or q")
        
        if choice == 'q':
            break
    
    print(f"\n📋 REVIEW SUMMARY:")
    for action, count in actions_taken.items():
        if count > 0:
            print(f"   {action.replace('_', ' ').title()}: {count}")


def generate_duplicate_prevention_report(folder_id=None):
    """Generate recommendations for preventing future duplicates"""
    print("🛡️ Generating duplicate prevention recommendations...")
    
    manager = MultiSheetManager(folder_id=folder_id)
    report = manager.find_all_duplicates(save_report=False)
    
    recommendations = {
        'current_duplicate_count': len(report['duplicates']) if report else 0,
        'recommendations': []
    }
    
    if report and report['duplicates']:
        # Analyze common duplicate patterns
        match_types = {}
        for dup in report['duplicates']:
            match_type = dup['match_info']['match_type']
            match_types[match_type] = match_types.get(match_type, 0) + 1
        
        # Generate recommendations based on patterns
        if 'exact' in match_types:
            recommendations['recommendations'].append({
                'priority': 'HIGH',
                'issue': 'Exact duplicate entries detected',
                'recommendation': 'Enable strict duplicate detection with "skip" action',
                'config_change': 'DUPLICATE_DETECTION_METHOD = "exact", DUPLICATE_ACTION = "skip"'
            })
        
        if 'fuzzy' in match_types:
            recommendations['recommendations'].append({
                'priority': 'MEDIUM',
                'issue': 'Similar entries with slight variations detected',
                'recommendation': 'Use fuzzy matching with appropriate threshold',
                'config_change': 'DUPLICATE_DETECTION_METHOD = "fuzzy", FUZZY_MATCH_THRESHOLD = 90'
            })
        
        if 'title_similarity' in match_types:
            recommendations['recommendations'].append({
                'priority': 'MEDIUM',
                'issue': 'Documents with similar titles detected',
                'recommendation': 'Enable title similarity checking',
                'config_change': 'ENABLE_FUZZY_TITLE_MATCHING = True, TITLE_SIMILARITY_THRESHOLD = 85'
            })
        
        recommendations['recommendations'].append({
            'priority': 'HIGH',
            'issue': 'Multiple duplicates found',
            'recommendation': 'Run regular duplicate scans and cleanup',
            'config_change': 'Schedule periodic execution of duplicate_manager.py --scan'
        })
    else:
        recommendations['recommendations'].append({
            'priority': 'LOW',
            'issue': 'No duplicates currently detected',
            'recommendation': 'Maintain current duplicate detection settings',
            'config_change': 'No changes needed'
        })
    
    print(f"\n🛡️ DUPLICATE PREVENTION RECOMMENDATIONS:")
    print(f"   Current duplicates: {recommendations['current_duplicate_count']}")
    
    for i, rec in enumerate(recommendations['recommendations'], 1):
        print(f"\n   {i}. [{rec['priority']}] {rec['issue']}")
        print(f"      → {rec['recommendation']}")
        print(f"      Config: {rec['config_change']}")
    
    return recommendations


def main():
    """Main command-line interface"""
    parser = argparse.ArgumentParser(description='Google Sheets Duplicate Management Tool')
    
    parser.add_argument('action', choices=['scan', 'clean', 'analyze', 'review', 'prevent'],
                      help='Action to perform')
    
    parser.add_argument('--folder-id', type=str, help='Google Drive folder ID')
    parser.add_argument('--output', type=str, help='Output file for reports')
    parser.add_argument('--method', choices=['exact', 'fuzzy', 'hash', 'multi'],
                      help='Duplicate detection method')
    parser.add_argument('--strategy', choices=['keep_first', 'keep_last'],
                      default='keep_first', help='Cleanup strategy')
    parser.add_argument('--dry-run', action='store_true', default=True,
                      help='Perform dry run (no actual changes)')
    parser.add_argument('--execute', action='store_true',
                      help='Actually execute changes (overrides --dry-run)')
    
    args = parser.parse_args()
    
    # Override dry_run if --execute is specified
    if args.execute:
        args.dry_run = False
    
    try:
        if args.action == 'scan':
            scan_for_duplicates(args.folder_id, args.output, args.method)
        
        elif args.action == 'clean':
            clean_duplicates(args.folder_id, args.strategy, args.dry_run)
        
        elif args.action == 'analyze':
            analyze_duplicate_patterns(args.folder_id)
        
        elif args.action == 'review':
            interactive_duplicate_review(args.folder_id)
        
        elif args.action == 'prevent':
            generate_duplicate_prevention_report(args.folder_id)
    
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
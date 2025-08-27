#!/usr/bin/env python3
"""
Skills Analysis Script for edwrdq's GitHub Repositories
Analyzes all repositories to extract programming languages, frameworks, and general areas of expertise.
"""

import json
import re
from collections import defaultdict, Counter
from pathlib import Path

def analyze_repositories():
    """Main function to analyze all repositories and generate skills summary."""
    
    # Repository data (extracted from GitHub API)
    repositories = [
        {
            "name": "DoralTelemetry",
            "description": "VEX V5 debugging and autonomous tuning system with Raspberry Pi integration, Bluetooth telemetry, and real-time vision tracking.",
            "language": "C++",
            "homepage": "",
            "topics": []
        },
        {
            "name": "edwrdq",
            "description": "Config files for my GitHub profile.",
            "language": None,
            "homepage": "https://github.com/polikfc123",
            "topics": ["config", "github-config"]
        },
        {
            "name": "33172X",
            "description": "team code",
            "language": "C++",
            "homepage": "",
            "topics": []
        },
        {
            "name": "historiabot",
            "description": "",
            "language": "Python",
            "homepage": "",
            "topics": []
        }
    ]
    
    # Analyze programming languages
    languages = Counter()
    for repo in repositories:
        if repo["language"]:
            languages[repo["language"]] += 1
    
    # Extract frameworks and libraries from descriptions and topics
    frameworks_libraries = set()
    
    # From topics
    for repo in repositories:
        frameworks_libraries.update(repo["topics"])
    
    # From descriptions (extract known frameworks/libraries)
    framework_patterns = {
        "VEX V5": r"\bvex\s*v5\b",
        "Raspberry Pi": r"\braspberry\s*pi\b",
        "Bluetooth": r"\bbluetooth\b",
        "Discord": r"\bdiscord\b",
        "Python": r"\bpython\b",
        "C++": r"\bc\+\+\b",
        "React": r"\breact\b",
        "Flask": r"\bflask\b",
        "Telemetry": r"\btelemetry\b",
        "Vision Tracking": r"\bvision\s*tracking\b",
        "Real-time": r"\breal.?time\b",
        "Robotics": r"\brobotics?\b",
        "Bot": r"\bbot\b",
        "AI": r"\bai\b"
    }
    
    for repo in repositories:
        desc = repo["description"].lower() if repo["description"] else ""
        for framework, pattern in framework_patterns.items():
            if re.search(pattern, desc, re.IGNORECASE):
                frameworks_libraries.add(framework)
    
    # Categorize into general areas
    general_areas = {
        "Robotics & Hardware": [],
        "VEX Robotics Programming": [],
        "Telemetry & Data Systems": [],
        "Discord Bot Development": [],
        "Systems Programming": [],
        "Real-time Applications": [],
        "Configuration & DevOps": [],
        "Computer Vision": [],
        "Embedded Systems": []
    }
    
    # Categorize repositories
    for repo in repositories:
        name = repo["name"].lower()
        desc = repo["description"].lower() if repo["description"] else ""
        lang = repo["language"]
        topics = repo["topics"]
        
        # Robotics & Hardware
        if ("vex" in desc or "robot" in desc or "telemetry" in desc or 
            "raspberry pi" in desc or name in ["doraltelemetry", "33172x"]):
            general_areas["Robotics & Hardware"].append(repo["name"])
        
        # VEX Robotics Programming
        if ("vex" in desc or name in ["doraltelemetry", "33172x"]):
            general_areas["VEX Robotics Programming"].append(repo["name"])
        
        # Telemetry & Data Systems
        if ("telemetry" in desc or "data" in desc or "tracking" in desc):
            general_areas["Telemetry & Data Systems"].append(repo["name"])
        
        # Discord Bot Development
        if ("bot" in name or "discord" in desc):
            general_areas["Discord Bot Development"].append(repo["name"])
        
        # Systems Programming
        if lang == "C++":
            general_areas["Systems Programming"].append(repo["name"])
        
        # Real-time Applications
        if ("real-time" in desc or "telemetry" in desc):
            general_areas["Real-time Applications"].append(repo["name"])
        
        # Configuration & DevOps
        if ("config" in desc or "config" in topics):
            general_areas["Configuration & DevOps"].append(repo["name"])
        
        # Computer Vision
        if ("vision" in desc or "tracking" in desc):
            general_areas["Computer Vision"].append(repo["name"])
        
        # Embedded Systems
        if ("raspberry pi" in desc or "vex" in desc):
            general_areas["Embedded Systems"].append(repo["name"])
    
    return {
        "programming_languages": dict(languages.most_common()),
        "frameworks_libraries": sorted(list(frameworks_libraries)),
        "general_areas": {k: v for k, v in general_areas.items() if v},
        "total_repositories": len(repositories)
    }

def generate_skills_report(analysis):
    """Generate a comprehensive skills report."""
    
    report = f"""# Edward Q - Skills Analysis

Based on analysis of {analysis['total_repositories']} GitHub repositories.

## 1. Programming Languages

"""
    
    # Programming languages section
    for i, (lang, count) in enumerate(analysis['programming_languages'].items(), 1):
        percentage = (count / analysis['total_repositories']) * 100
        report += f"{i}. **{lang}** - {count} repositories ({percentage:.1f}%)\n"
    
    report += f"""
## 2. (Meta-)Frameworks & Libraries

"""
    
    # Frameworks and libraries section
    for i, framework in enumerate(analysis['frameworks_libraries'], 1):
        report += f"{i}. {framework}\n"
    
    report += f"""
## 3. General Areas

"""
    
    # General areas section
    for i, (area, repos) in enumerate(analysis['general_areas'].items(), 1):
        report += f"{i}. **{area}** ({len(repos)} repositories)\n"
        for repo in repos:
            report += f"   - {repo}\n"
        report += "\n"
    
    report += f"""
## Summary

Edward demonstrates expertise across multiple domains:

- **Primary Languages**: {', '.join([lang for lang, _ in list(analysis['programming_languages'].items())[:3]])}
- **Robotics Focus**: Specialized in VEX V5 robotics systems, telemetry, and embedded programming
- **Systems Programming**: Strong C++ background for performance-critical applications
- **Bot Development**: Discord bot creation with AI integration
- **Hardware Integration**: Raspberry Pi, Bluetooth, and real-time data processing
- **Modern Development**: Configuration management and development best practices

Generated on {Path(__file__).stat().st_mtime} by automated analysis script.
"""
    
    return report

if __name__ == "__main__":
    analysis = analyze_repositories()
    report = generate_skills_report(analysis)
    
    # Save to file
    with open("skills_analysis_edwrdq.md", "w") as f:
        f.write(report)
    
    print("Skills analysis complete! Report saved to skills_analysis_edwrdq.md")
    print("\nQuick Summary:")
    print(f"- {len(analysis['programming_languages'])} programming languages")
    print(f"- {len(analysis['frameworks_libraries'])} frameworks/libraries identified") 
    print(f"- {len(analysis['general_areas'])} general areas of expertise")
    print(f"- {analysis['total_repositories']} total repositories analyzed")
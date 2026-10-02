"""Resolve only supported explicit time expressions, at the ORIGINAL observation.

The model quotes a time expression; it cannot silently supply an arbitrary date.
Vague dates stay unresolved. This parser is an engineered language subset, not a
claim of general Chinese temporal understanding. All internal times are UTC.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
import math,re


def timestamp(value):
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=253402214400:
        raise ValueError('时间必须是有限的UTC时间戳')
    return round(float(value),6)


def tzinfo(name):
    if not isinstance(name,str):raise ValueError('需要时区')
    if name in ('UTC','Z'):return timezone.utc
    m=re.fullmatch(r'(?:UTC)?([+-])(\d{2}):(\d{2})',name)
    if m:
        h,n=int(m[2]),int(m[3])
        if h>14 or n>59 or h==14 and n:raise ValueError('UTC偏移无效')
        return timezone((1 if m[1]=='+' else -1)*timedelta(hours=h,minutes=n))
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except (KeyError,ValueError):
        raise ValueError('此电脑没有该时区数据；请安装tzdata，或明确选择UTC±HH:MM固定偏移（不自动切换夏令时）') from None


def iso(at,tz='UTC'):
    return datetime.fromtimestamp(timestamp(at),tzinfo(tz)).isoformat(timespec='seconds')


def number(s):
    if s.isdigit():return int(s)
    digits={v:i for i,v in enumerate('零一二三四五六七八九')};digits['两']=2
    if s in digits:return digits[s]
    if '十' in s:
        a,b=s.split('十',1);return (digits.get(a,1)*10)+digits.get(b,0)
    raise ValueError('数字表达暂不支持')


def resolve_when(expression,at,tz='UTC'):
    """Return epoch seconds or None. Never invent a time for 'sometime/afternoon'."""
    if not isinstance(expression,str) or len(expression)>240:raise ValueError('时间原文过长')
    s=expression.strip();zone=tzinfo(tz);base=datetime.fromtimestamp(timestamp(at),zone)
    if not s:return None
    try:
        d=datetime.fromisoformat(s.replace('Z','+00:00'))
        if d.tzinfo is not None:return timestamp(d.timestamp())
    except ValueError:pass
    m=re.fullmatch(r'([0-9零一二三四五六七八九十两]+)\s*(秒钟?|分钟|小时|天)(?:以?后|之后)',s)
    if m:
        amount=number(m[1]);unit=m[2];scale=1 if unit.startswith('秒') else 60 if unit=='分钟' else 3600 if unit=='小时' else 86400
        if not 1<=amount<=366:return None
        return timestamp(at+amount*scale)
    # Explicit date/day plus exact clock; no implied day for a bare '8点'.
    day=None;rest=s
    m=re.match(r'^(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})日?\s*',s)
    if m:
        try:day=base.replace(year=int(m[1]),month=int(m[2]),day=int(m[3]))
        except ValueError:return None
        rest=s[m.end():]
    else:
        for label,delta in [('今天',0),('今晚',0),('明天',1),('明晚',1),('后天',2)]:
            if s.startswith(label):day=base+timedelta(days=delta);rest=s[len(label):];rest=('晚上'+rest) if label.endswith('晚') else rest;break
        if day is None:
            m=re.match(r'^(下周|本周|这周|周|星期)([一二三四五六日天])',s)
            if m:
                target='一二三四五六日'.index('日' if m[2]=='天' else m[2]);diff=target-base.weekday()
                if m[1]=='下周':diff+=7
                elif m[1] in ('周','星期') and diff<0:diff+=7
                day=base+timedelta(days=diff);rest=s[m.end():]
    if day is None:return None
    m=re.fullmatch(r'\s*(上午|早上|下午|晚上|中午)?\s*([0-9零一二三四五六七八九十两]{1,3})(?::([0-5]?\d)|[点时](?:([0-5]?\d)分?|半)?)\s*(?:左右|前后)?',rest)
    if not m:return None
    hour=number(m[2]);minute=int(m[3] or m[4] or (30 if '半' in rest else 0))
    if m[1] in ('下午','晚上') and 1<=hour<12:hour+=12
    if m[1]=='中午' and hour<11:hour+=12
    if hour>23 or minute>59:return None
    candidate=day.replace(hour=hour,minute=minute,second=0,microsecond=0)
    # DST gaps and ambiguous folds must be clarified, not arbitrarily selected.
    if candidate.replace(fold=0).utcoffset()!=candidate.replace(fold=1).utcoffset():return None
    roundtrip=datetime.fromtimestamp(candidate.timestamp(),zone)
    if roundtrip.replace(tzinfo=None)!=candidate.replace(tzinfo=None):return None
    return timestamp(candidate.timestamp())

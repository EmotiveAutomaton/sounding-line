"""Conservative, identity-free wikitext-to-final-text boundary for T2.r.

No lineage, rewrite labels, live retrieval or scientific launch lives here.
Unsupported syntax is a counted source failure, never silently plain text.
This is a proposed parser subset, not a MediaWiki renderer-equivalence claim.
"""
from collections import Counter
from html import unescape
from html.parser import HTMLParser
import re
from runners.stage9.coauthor import units
from . import week4_revision_source_h1 as revision
from .week4_revision_utf16_h1 import text_of


class ParseBoundary(ValueError):
    """Message is a fixed reason code; it never contains source text or IDs."""


DROP_TAGS = {'ref', 'references', 'table'}
TEXT_TAGS = {'span', 'small', 'big', 'sup', 'sub', 'i', 'b', 'u', 's',
             'em', 'strong', 'div', 'p', 'blockquote', 'poem'}
VOID_TAGS = {'br', 'hr'}


class VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out, self.stack, self.dropping = [], [], []
        self.counts = Counter()

    def handle_starttag(self, tag, attrs):
        if self.dropping:
            if tag not in VOID_TAGS:
                self.dropping.append(tag)
            return
        if tag in DROP_TAGS:
            self.dropping.append(tag)
            self.counts['dropped_' + tag] += 1
            self.out.append(' ')
        elif tag in TEXT_TAGS:
            self.stack.append(tag)
            if tag in {'div', 'p', 'blockquote', 'poem'}:
                self.out.append('\n')
        elif tag in VOID_TAGS:
            self.out.append('\n')
        else:
            raise ParseBoundary('unsupported_html_tag')

    def handle_startendtag(self, tag, attrs):
        if self.dropping:
            return
        if tag in DROP_TAGS:
            self.counts['dropped_' + tag] += 1
            self.out.append(' ')
        elif tag in VOID_TAGS | TEXT_TAGS:
            self.out.append(' ')
        else:
            raise ParseBoundary('unsupported_self_closing_tag')

    def handle_endtag(self, tag):
        if self.dropping:
            if self.dropping[-1] != tag:
                raise ParseBoundary('mismatched_dropped_html_tag')
            self.dropping.pop()
            return
        if not self.stack or self.stack[-1] != tag:
            raise ParseBoundary('mismatched_html_tag')
        self.stack.pop()
        if tag in {'div', 'p', 'blockquote', 'poem'}:
            self.out.append('\n')

    def handle_data(self, data):
        if not self.dropping:
            self.out.append(data)

    def handle_entityref(self, name):
        self.handle_data('&' + name + ';')

    def handle_charref(self, name):
        self.handle_data('&#' + name + ';')

    def handle_comment(self, data):
        self.counts['dropped_comments'] += 1

    def handle_decl(self, decl):
        raise ParseBoundary('unsupported_declaration')

    def unknown_decl(self, data):
        raise ParseBoundary('unsupported_declaration')

    def handle_pi(self, data):
        raise ParseBoundary('unsupported_processing_instruction')

    def finish(self):
        self.close()
        if self.stack or self.dropping:
            raise ParseBoundary('unclosed_html_tag')
        return ''.join(self.out), self.counts


def stripped_balanced(text, opening, closing, counter, key):
    result, i, depth = [], 0, 0
    while i < len(text):
        if text.startswith(opening, i):
            if depth == 0:
                result.append(' ')
                counter[key] += 1
            depth += 1
            i += len(opening)
        elif text.startswith(closing, i):
            if depth == 0:
                raise ParseBoundary('orphan_balanced_closer')
            depth -= 1
            i += len(closing)
        else:
            if depth == 0:
                result.append(text[i])
            i += 1
    if depth:
        raise ParseBoundary('unclosed_balanced_markup')
    return ''.join(result)


def templates(text, counts):
    result, stack, i = [], [], 0
    while i < len(text):
        if text.startswith('{{', i):
            width = 3 if text.startswith('{{{', i) else 2
            if not stack:
                result.append(' ')
                counts['dropped_variables' if width == 3 else 'dropped_templates'] += 1
            stack.append(width)
            i += width
        elif text.startswith('}}', i):
            if not stack:
                raise ParseBoundary('orphan_template_closer')
            width = stack.pop()
            if not text.startswith('}' * width, i):
                raise ParseBoundary('mismatched_template_closer')
            i += width
        else:
            if not stack:
                result.append(text[i])
            i += 1
    if stack:
        raise ParseBoundary('unclosed_template')
    return ''.join(result)


def links(text, counts):
    out, i = [], 0
    while i < len(text):
        if text.startswith('[[', i):
            stop = text.find(']]', i + 2)
            if stop < 0 or '[[' in text[i + 2:stop]:
                raise ParseBoundary('unclosed_or_nested_internal_link')
            body = text[i + 2:stop]
            parts = body.split('|')
            target = parts[0].strip()
            if not target or any(c in target for c in '\r\n'):
                raise ParseBoundary('invalid_link_target')
            namespace = target.lstrip(':').split(':', 1)[0].casefold() if ':' in target else None
            if namespace in {'file', 'image', 'category'}:
                # A leading colon makes a category/file reference a visible link.
                if not target.startswith(':'):
                    out.append(' ')
                    counts['dropped_nonprose_links'] += 1
                    i = stop + 2
                    continue
            if namespace and namespace not in {'file', 'image', 'category', 'w', 'wikipedia'}:
                raise ParseBoundary('unregistered_link_namespace')
            label = parts[-1] if len(parts) > 1 else target.lstrip(':').replace('_', ' ')
            if not label.strip() or '|' in label or '[' in label or ']' in label:
                raise ParseBoundary('unsupported_link_label')
            out.append(label)
            counts['visible_internal_links'] += 1
            i = stop + 2
        elif text.startswith(']]', i):
            raise ParseBoundary('orphan_internal_link_closer')
        elif text[i] == '[' and re.match(r'(?:https?://|//)', text[i + 1:]):
            stop = text.find(']', i + 1)
            if stop < 0:
                raise ParseBoundary('unclosed_external_link')
            body = text[i + 1:stop]
            if '[' in body:
                raise ParseBoundary('nested_external_link')
            parts = body.split(None, 1)
            out.append(parts[1] if len(parts) == 2 else ' ')
            counts['external_links'] += 1
            i = stop + 1
        else:
            out.append(text[i])
            i += 1
    return ''.join(out)


def clean_wikitext(text):
    if not isinstance(text, str):
        raise ParseBoundary('source_not_text')
    if len(text.encode('utf8')) > 32 * 1024**2:
        raise ParseBoundary('source_text_cap')
    parser = VisibleHTML()
    parser.feed(text)
    text, counts = parser.finish()
    if re.search(r'<\s*[A-Za-z!/]', text):
        raise ParseBoundary('unparsed_html_boundary')
    # Triple-brace variables and parser functions are not a renderable template
    # expansion. They are removed as template syntax, with their own count.
    text = templates(text, counts)
    text = stripped_balanced(text, '{|', '|}', counts, 'dropped_tables')
    text = links(text, counts)
    if re.search(r'\{\{|\}\}|\{\||\|\}|__\w+__|~{3,}', text):
        raise ParseBoundary('unresolved_structural_markup')
    # HTML entities decode after structural parsing; escaped markup stays text.
    text = unescape(text)
    text = re.sub(r"'{2,5}", '', text)
    lines = []
    for line in text.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        line = re.sub(r'^\s*=+\s*(.*?)\s*=+\s*$', r'\1', line)
        line = re.sub(r'^\s*[*#;:]+\s*', '', line)
        line = re.sub(r'[ \t\u00a0]+', ' ', line).strip()
        if line:
            lines.append(line)
    return '\n'.join(lines), dict(sorted(counts.items()))


def final_sentences(final_wikitext):
    """Final text alone, using the unchanged CoAuthor sentence boundary rule."""
    text, removed = clean_wikitext(final_wikitext)
    document = units(text)
    spans = revision.sentences(document, [None] * len(document))
    rows = []
    for index, span in enumerate(spans):
        value = text_of(document[span['content_start_utf16']:span['content_end_utf16']])
        if value.strip():
            rows.append(dict(index=index, text=value, position=index/max(1, len(spans)-1),
                             complete=span['complete']))
    return dict(sentences=rows, removed=removed,
                parser_scope='conservative_supported_markup_subset',
                labels_computed=False, feature_time='final_current_version')

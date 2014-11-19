/**
 * $Id: editor_plugin_src.js 2009-05-10
 *
 * @author Ubernote/Shane Tomlinson
 * http://www.ubernote.com
 * set117@gmail.com
 *
 * Detect emails and urls as they are typed in Mozilla/Safari/Chrome and Opera
 * Borrowed from both Typo3 http://typo3.org/ and Xinha http://xinha.gogo.co.nz/
 * Heavily modified and cleaned up.
 * 
 * Original license info from Xinha at the bottom.
 */

(function() {
	tinymce.create('tinymce.plugins.LinkAutoDetect', {
		init : function(ed, url) {
			var t = this;
			t.RE_email = /^[a-z0-9_\-]+(\.[_a-z0-9\-]+)*@([_a-z0-9\-]+\.)+([a-z]{2}|aero|arpa|biz|com|coop|edu|gov|info|int|jobs|mil|museum|name|nato|net|org|pro|travel)$/i;
			t.RE_url   = /^((https?|ftp|news):\/\/)?([a-z]([a-z0-9\-]*\.)+([a-z]{2}|aero|arpa|biz|com|coop|edu|gov|info|int|jobs|mil|museum|name|nato|net|org|pro|travel)|(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))(\/[a-z0-9_\-\.~]+)*(\/([a-z0-9_\-\.]*)(\?[a-z0-9+_\-\.%=&amp;]*)?)?(#[a-z][a-z0-9_]*)?$/i;
			ed.onKeyPress.add( t.onKeyPress, t );
			ed.onKeyUp.add( t.onKeyUp, t );
		},
		
		getInfo : function() {
			return {
				longname : 'Link Auto Detect',
				author : 'Ubernote/Shane Tomlinson',
				authorurl : 'http://www.ubernote.com',
				infourl : 'http://www.ubernote.com',
				version : '0.2'
			};
		},
		
		onKeyPress : function(ed, ev, o) {
			if(tinymce.isIE) {   
				// IE already does auto-detect, so no worries.
				return;
			} // end if
			
			var s = ed.selection.getSel();
			var textNode = s.anchorNode;
			
			var createLink = function (searchfor, hlink, midStart) {
				var leftText  = textNode;
				var rightText = leftText.splitText(s.anchorOffset);
				var midText   = leftText.splitText(midStart);
				var midEnd = midText.data.search(searchfor);
				if (midEnd != -1) {
					rightText = midText.splitText(midEnd);
				} // end if
				var tag = ed.dom.create('a', { href: hlink }, midText.data);
				var a = midText.parentNode.insertBefore(tag, rightText);
				
				// We are going to put the cursor into the first position after
				//  the anchor and let the browser take care of inserting the space/enter.
				s.collapse(rightText, 0);
				ed.dom.remove(midText);
			};
			
			// Space or Enter, see if the text just typed looks like a URL, or email address and link it accordingly
			if((ev.which == 13 || ev.which == 32) 
				&& textNode.nodeType == 3 && textNode.data.length > 3 
				&& textNode.data.indexOf('.') >= 0 && !ed.dom.getParent(textNode, 'a')) {
				var midStart = textNode.data.substring(0,s.anchorOffset).search(/\S{4,}$/);
				if(midStart != -1) {
					var matchData = textNode.data.substring(0,s.anchorOffset).replace(/^.*?(\S*)$/, '$1');
					var matchURL = matchData.match(this.RE_url);
					var matchEmail = matchData.match(this.RE_email);
					if(matchEmail) {
						createLink(/[^a-zA-Z0-9\.@_\-]/, 'mailto:' + matchEmail[0], midStart);
					}
					else if(matchURL) {
						createLink( /[^a-zA-Z0-9\._\-\/\&\?#=:@]/, (matchURL[1] ? '' : 'http://') + matchURL[0], midStart);
					}
				} // end if
			}
		},
		
		onKeyUp : function(ed, ev, o) {
			if(tinymce.isIE) {   
				// IE already does auto-detect, so no worries.
				return;
			} // end if
			
			var s = ed.selection.getSel();
			var textNode = s.anchorNode;
				var a = ed.dom.getParent(textNode, 'a');
				
				if( ! (ev.which && ( ev.which == 13 || ev.which == 32)) 
					&& (ev.which || ev.keyCode == 8 || ev.keyCode == 46)
					&& (textNode.nodeType == 3) && (a)) {
					// See if we might be changing a link
					var matchEmail = s.anchorNode.data.match(this.RE_email);
					var matchURL = textNode.data.match(this.RE_url);
					if(matchEmail) {
						ed.dom.setAttrib(a, 'href', 'mailto:' + textNode.data);
					} // end if
					if(matchURL) {
						ed.dom.setAttrib(a, 'href', (matchURL[1] ? '' : 'http://') + matchURL[0]);
					} // end if
				} // end if
			}
	});

	// Register plugin
	tinymce.PluginManager.add('linkautodetect', tinymce.plugins.LinkAutoDetect);
})();

/*
htmlArea License (based on BSD license)
Copyright (c) 2002-2004, interactivetools.com, inc.
Copyright (c) 2003-2004 dynarch.com
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1) Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2) Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3) Neither the name of interactivetools.com, inc. nor the names of its
   contributors may be used to endorse or promote products derived from this
   software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
*/
(function() {
	tinymce.create('tinymce.plugins.LinkAutoDetect', {
		init : function(ed, url) {
			var t = this; t.RE_email = /^[a-z0-9_\-]+(\.[_a-z0-9\-]+)*@([_a-z0-9\-]+\.)+([a-z]{2}|aero|arpa|biz|com|coop|edu|gov|info|int|jobs|mil|museum|name|nato|net|org|pro|travel)$/i; t.RE_url   = /^((https?|ftp|news):\/\/)?([a-z]([a-z0-9\-]*\.)+([a-z]{2}|aero|arpa|biz|com|coop|edu|gov|info|int|jobs|mil|museum|name|nato|net|org|pro|travel)|(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))(\/[a-z0-9_\-\.~]+)*(\/([a-z0-9_\-\.]*)(\?[a-z0-9+_\-\.%=&amp;]*)?)?(#[a-z][a-z0-9_]*)?$/i;ed.onKeyPress.add( t.onKeyPress, t );ed.onKeyUp.add( t.onKeyUp, t );
		},
		getInfo : function() {
			return { longname : 'Link Auto Detect', author : 'Ubernote/Shane Tomlinson', authorurl : 'http://www.ubernote.com',infourl : 'http://www.ubernote.com',version : '0.2'};
		},
		onKeyPress : function(ed, ev, o) {
			if(tinymce.isIE) {   
				return;
			}
			var s = ed.selection.getSel();
			var textNode = s.anchorNode;
			var createLink = function (searchfor, hlink, midStart) {
				var leftText  = textNode;
				var rightText = leftText.splitText(s.anchorOffset);
				var midText   = leftText.splitText(midStart);
				var midEnd = midText.data.search(searchfor);
				if (midEnd != -1) {
					rightText = midText.splitText(midEnd);
				}
				var tag = ed.dom.create('a', { href: hlink }, midText.data);
				var a = midText.parentNode.insertBefore(tag, rightText);
				s.collapse(rightText, 0);
				ed.dom.remove(midText);
			};
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
				}
			}
		},
		onKeyUp : function(ed, ev, o) {
			if(tinymce.isIE) {   
				return;
			}
			
			var s = ed.selection.getSel();
			var textNode = s.anchorNode;
				var a = ed.dom.getParent(textNode, 'a');
				
				if( ! (ev.which && ( ev.which == 13 || ev.which == 32)) 
					&& (ev.which || ev.keyCode == 8 || ev.keyCode == 46)
					&& (textNode.nodeType == 3) && (a)) {
					var matchEmail = s.anchorNode.data.match(this.RE_email);
					var matchURL = textNode.data.match(this.RE_url);
					if(matchEmail) {
						ed.dom.setAttrib(a, 'href', 'mailto:' + textNode.data);
					}
					if(matchURL) {
						ed.dom.setAttrib(a, 'href', (matchURL[1] ? '' : 'http://') + matchURL[0]);
					}
				}
			}
	});
	tinymce.PluginManager.add('linkautodetect', tinymce.plugins.LinkAutoDetect);
})();
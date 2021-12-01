var PageIndex = function(div, url) {
    $(div).append('<ul/>');
    var root = div.find('ul:last');
    var size = 15; // Number of pages to be shown in the index.
    var total = 1; // Total number of list entries.
    var per_page = 25; // List entries per page.
    var offset = 0;

    this._add_li = function(text, is_link, is_active, theoffset) {
        root.append('<li/>');
        var li = root.find('li:last');

        if (is_active)
            li.addClass('active');

        if (!is_link) {
            li.text(text);
            return li;
        }

        li.append('<a/>');
        var link = li.find('a:last');
        link.attr('href', url + '?' + $.param({'offset': theoffset}));
        link.text(text);
        return link;
    };

    this._add_all = function() {
      var n_pages = Math.max(1, Math.ceil(total / per_page));
      var active_page = Math.ceil(offset / per_page) + 1;
    
      // Find the first number to show in the index.
      var index_offset = 1;
      if (active_page > size / 2)
          index_offset = Math.max(1, active_page - Math.ceil(size / 2));
      if (index_offset + size > n_pages)
          index_offset = Math.max(1, n_pages - size);
    
      // Show the << link to the previous page.
      if (active_page == 1)
          this._add_li('<<');
      else
          this._add_li('<<', true, false, per_page * (active_page - 2));
    
      // Always show a link to the first page.
      if (index_offset > 1)
          this._add_li('1', true, active_page == 1, 0);
      if (index_offset > 2)
          this._add_li('...');
    
      // Print the numbers.
      for (var i = index_offset; i <= index_offset + size && i <= n_pages; i++) {
          if (i == active_page)
              this._add_li(i, false, true);
          else
              this._add_li(i, true, false, (i - 1) * per_page);
      }
    
      // Always show a link to the last page.
      if (index_offset + size < n_pages - 1)
          this._add_li('...');
      if (index_offset + size < n_pages)
          this._add_li(n_pages, true, n_pages == active_page, (n_pages - 1) * per_page);
    
      // Show the >> link to the next page.
      if (active_page >= n_pages)
          this._add_li('>>');
      else
          this._add_li('>>', true, false, per_page * active_page);
    };

    this.set_size = function(thesize) {
        size = thesize;
        this.refresh();
    };

    this.set_entries_per_page = function(epp) {
        per_page = epp;
        this.refresh();
    };

    this.set_total = function(thetotal) {
        total = thetotal;
        this.refresh();
    };

    this.set_offset = function(theoffset) {
        offset = theoffset;
        this.refresh();
    };

    this.refresh = function() {
        root.empty();
        this._add_all();
    };

    this.update = function(thetotal, theoffset) {
        total = thetotal;
        offset = theoffset;
        this.refresh();
    };
}

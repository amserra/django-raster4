from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render

from .models import Legend, LegendEntry, LegendSemantics, RasterLayer, RasterLayerMetadata, RasterTile


class FilenameActionForm(forms.Form):
    """
    Form for changing the filename of a raster.
    """
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    path = forms.CharField(label='Filepath', required=False)


class RasterLayerModelAdmin(admin.ModelAdmin):
    """
    Admin action to update filepaths only. Files can be uploadded to the
    filesystems through any channel and then files can be assigned to the
    raster objects through this action. This might be useful for large raster
    files.
    """
    readonly_fields = ('parse_log',)
    actions = ['reparse_rasters', 'manually_update_filepath']

    def reparse_rasters(self, request, queryset):
        """
        Admin action to re-parse a set of rasterlayers.
        """
        for rasterlayer in queryset:
            rasterlayer.parse_log = ''
            rasterlayer.save()

        msg = 'Parsing Rasters, check parse logs for progress'
        self.message_user(request, msg)

    def manually_update_filepath(self, request, queryset):
        """
        Admin action to change filepath without uploading new file.
        """
        form = None
        layer = queryset[0]

        # Check if layer already has a file specified
        if layer.rasterfile:
            self.message_user(
                request,
                "This layer already has a file specified. Remove file from layer before specifying new path.",
                level=messages.ERROR
            )
            return

        # After posting, set the new name to file field
        if 'apply' in request.POST:
            form = FilenameActionForm(request.POST)
            if form.is_valid():
                path = form.cleaned_data['path']
                layer.rasterfile.name = path
                layer.save()
                self.message_user(request, "Successfully updated path.")
                return HttpResponseRedirect(request.get_full_path())

        # Before posting, prepare empty action form
        if not form:
            form = FilenameActionForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})

        return render(request, 'raster/updatepath.html', {'items': queryset, 'form': form, 'title': u'Update Path'})


class RasterLayerMetadataModelAdmin(admin.ModelAdmin):
    readonly_fields = ('rasterlayer', 'uperleftx', 'uperlefty',
                       'width', 'height', 'scalex', 'scaley', 'skewx',
                       'skewy', 'numbands')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RasterTileModelAdmin(admin.ModelAdmin):
    readonly_fields = ('rast', 'rasterlayer', 'filename', 'is_base', 'tilex',
                       'tiley', 'tilez')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class LegendEntriesInLine(admin.TabularInline):
    model = Legend.entries.through


class LegendAdmin(admin.ModelAdmin):
    inlines = (
        LegendEntriesInLine,
    )

admin.site.register(LegendSemantics)
admin.site.register(RasterLayer, RasterLayerModelAdmin)
admin.site.register(RasterTile, RasterTileModelAdmin)
admin.site.register(RasterLayerMetadata, RasterLayerMetadataModelAdmin)
admin.site.register(LegendEntry)
admin.site.register(Legend, LegendAdmin)

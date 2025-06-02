import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.user_settings import get_user_settings, update_user_setting
from utils.thumbnails import get_user_thumbnail_path

logger = logging.getLogger(__name__)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command."""
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)
    
    # Get thumbnail for display
    thumbnail_path = get_user_thumbnail_path(user_id)
    
    # Create settings text
    settings_text = f"""
⚙️ **Settings for** `{update.effective_user.first_name}` ⚙️

📤 Upload as {settings['upload_mode'].title()}
🖼️ Custom Thumbnail {'Exists' if settings['custom_thumbnail'] else 'Not Exists'}
📺 Resolution is {settings['resolution']}p
🎬 Vcodec is {settings['vcodec']}
🎨 Bits is {settings['bits']} Bits
📐 Aspect Ratio is {settings['aspect_ratio']}
🔧 CRF is {settings['crf']}
📋 Metadata is {'Enabled' if settings['metadata_enabled'] else 'Disabled'}
💧 Watermark is {'Set' if settings['watermark'] else 'None'}
📝 Auto Rename is {'Set' if settings['auto_rename'] else 'None'}
"""
    
    # Create inline keyboard
    keyboard = [
        [InlineKeyboardButton(f"Upload Mode | {settings['upload_mode'].title()}", callback_data="toggle_upload_mode")],
        [
            InlineKeyboardButton("Resolution", callback_data="set_resolution"),
            InlineKeyboardButton("Vcodec", callback_data="set_vcodec")
        ],
        [
            InlineKeyboardButton("Bits", callback_data="set_bits"),
            InlineKeyboardButton("CRF", callback_data="set_crf")
        ],
        [
            InlineKeyboardButton("Set Metadata", callback_data="set_metadata"),
            InlineKeyboardButton("Set Watermark", callback_data="set_watermark")
        ],
        [
            InlineKeyboardButton("Thumbnail ✅" if settings['custom_thumbnail'] else "Set Thumbnail", callback_data="set_thumbnail"),
            InlineKeyboardButton("Aspect 16:9 ✅", callback_data="set_aspect_ratio")
        ],
        [InlineKeyboardButton("Set Auto Rename", callback_data="set_auto_rename")],
        [InlineKeyboardButton("❌ CLOSE", callback_data="close_settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send photo with settings
    if thumbnail_path:
        try:
            with open(thumbnail_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=settings_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except:
            await update.message.reply_text(
                settings_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from settings menu."""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    await query.answer()
    
    if data == "close_settings":
        try:
            await query.edit_message_caption(caption="Settings closed.")
        except:
            try:
                await query.edit_message_text(text="Settings closed.")
            except Exception as e:
                logger.error(f"Error closing settings: {e}")
        return
    
    elif data == "toggle_upload_mode":
        settings = get_user_settings(user_id)
        new_mode = "video" if settings['upload_mode'] == "document" else "document"
        update_user_setting(user_id, 'upload_mode', new_mode)
        await refresh_settings_menu(query, user_id)
    
    elif data == "set_resolution":
        await show_resolution_menu(query, user_id)
    
    elif data == "set_vcodec":
        await show_vcodec_menu(query, user_id)
    
    elif data == "set_bits":
        await show_bits_menu(query, user_id)
    
    elif data == "set_crf":
        await show_crf_menu(query, user_id)
    
    elif data == "set_thumbnail":
        await handle_thumbnail_setting(query, user_id)
    
    elif data == "set_aspect_ratio":
        await show_aspect_ratio_menu(query, user_id)
    
    elif data.startswith("res_"):
        resolution = data.split("_")[1]
        update_user_setting(user_id, 'resolution', resolution)
        await refresh_settings_menu(query, user_id)
    
    elif data.startswith("vcodec_"):
        vcodec = data.split("_")[1]
        update_user_setting(user_id, 'vcodec', vcodec)
        await refresh_settings_menu(query, user_id)
    
    elif data.startswith("bits_"):
        bits = data.split("_")[1]
        update_user_setting(user_id, 'bits', bits)
        await refresh_settings_menu(query, user_id)
    
    elif data.startswith("crf_"):
        crf = data.split("_")[1]
        update_user_setting(user_id, 'crf', crf)
        await refresh_settings_menu(query, user_id)
    
    elif data.startswith("aspect_"):
        aspect_ratio = data.split("_")[1]
        update_user_setting(user_id, 'aspect_ratio', aspect_ratio)
        await refresh_settings_menu(query, user_id)
    
    elif data == "back_to_settings":
        await refresh_settings_menu(query, user_id)
    
    elif data == "delete_thumbnail":
        from utils.thumbnails import delete_user_thumbnail
        success = delete_user_thumbnail(user_id)
        if success:
            update_user_setting(user_id, 'custom_thumbnail', None)
        await refresh_settings_menu(query, user_id)
    
    # Handle coming soon features
    elif data in ["set_metadata", "set_watermark", "set_auto_rename"]:
        try:
            await query.edit_message_caption(
                caption="🚧 **Feature Coming Soon** 🚧\n\nThis feature is under development and will be available in the next update!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_to_settings")]])
            )
        except:
            try:
                await query.edit_message_text(
                    text="🚧 **Feature Coming Soon** 🚧\n\nThis feature is under development and will be available in the next update!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_to_settings")]])
                )
            except Exception as e:
                logger.error(f"Error showing coming soon message: {e}")

async def show_resolution_menu(query, user_id):
    """Show resolution selection menu."""
    keyboard = [
        [
            InlineKeyboardButton("1080p", callback_data="res_1080"),
            InlineKeyboardButton("720p", callback_data="res_720"),
            InlineKeyboardButton("576p", callback_data="res_576")
        ],
        [
            InlineKeyboardButton("480p", callback_data="res_480"),
            InlineKeyboardButton("360p", callback_data="res_360"),
            InlineKeyboardButton("240p", callback_data="res_240")
        ],
        [
            InlineKeyboardButton("Back", callback_data="back_to_settings"),
            InlineKeyboardButton("Close", callback_data="close_settings")
        ]
    ]
    
    try:
        await query.edit_message_caption(
            caption="Choose from Below Buttons",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        try:
            await query.edit_message_text(
                text="Choose from Below Buttons",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error showing resolution menu: {e}")

async def show_vcodec_menu(query, user_id):
    """Show video codec selection menu."""
    keyboard = [
        [InlineKeyboardButton("x264", callback_data="vcodec_x264")],
        [InlineKeyboardButton("x265", callback_data="vcodec_x265")],
        [
            InlineKeyboardButton("Back", callback_data="back_to_settings"),
            InlineKeyboardButton("Close", callback_data="close_settings")
        ]
    ]
    
    try:
        await query.edit_message_caption(
            caption="Choose from Below Buttons",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        try:
            await query.edit_message_text(
                text="Choose from Below Buttons",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error showing vcodec menu: {e}")

async def show_bits_menu(query, user_id):
    """Show bit depth selection menu."""
    keyboard = [
        [InlineKeyboardButton("10 Bits", callback_data="bits_10")],
        [InlineKeyboardButton("8 Bits", callback_data="bits_8")],
        [
            InlineKeyboardButton("Back", callback_data="back_to_settings"),
            InlineKeyboardButton("Close", callback_data="close_settings")
        ]
    ]
    
    try:
        await query.edit_message_caption(
            caption="Choose from Below Buttons",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        try:
            await query.edit_message_text(
                text="Choose from Below Buttons",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error showing bits menu: {e}")

async def show_crf_menu(query, user_id):
    """Show CRF selection menu."""
    # Create buttons for CRF 21-40
    keyboard = []
    
    # Create rows of 4 buttons each
    for i in range(21, 41, 4):
        row = []
        for j in range(4):
            if i + j <= 40:
                row.append(InlineKeyboardButton(str(i + j), callback_data=f"crf_{i + j}"))
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("Back", callback_data="back_to_settings"),
        InlineKeyboardButton("Close", callback_data="close_settings")
    ])
    
    try:
        await query.edit_message_caption(
            caption="Choose from Below Buttons",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        try:
            await query.edit_message_text(
                text="Choose from Below Buttons",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error showing CRF menu: {e}")

async def show_aspect_ratio_menu(query, user_id):
    """Show aspect ratio selection menu."""
    keyboard = [
        [InlineKeyboardButton("16:9", callback_data="aspect_16:9")],
        [InlineKeyboardButton("4:3", callback_data="aspect_4:3")],
        [
            InlineKeyboardButton("Back", callback_data="back_to_settings"),
            InlineKeyboardButton("Close", callback_data="close_settings")
        ]
    ]
    
    try:
        await query.edit_message_caption(
            caption="Choose from Below Buttons",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        try:
            await query.edit_message_text(
                text="Choose from Below Buttons",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error showing aspect ratio menu: {e}")

async def handle_thumbnail_setting(query, user_id):
    """Handle thumbnail setting."""
    settings = get_user_settings(user_id)
    
    if settings['custom_thumbnail']:
        # Show delete option if thumbnail exists
        keyboard = [
            [InlineKeyboardButton("Delete Thumbnail", callback_data="delete_thumbnail")],
            [
                InlineKeyboardButton("Back", callback_data="back_to_settings"),
                InlineKeyboardButton("Close", callback_data="close_settings")
            ]
        ]
        
        try:
            await query.edit_message_caption(
                caption="Send a photo to save it as custom thumbnail.\nTimeout: 60 sec",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            try:
                await query.edit_message_text(
                    text="Send a photo to save it as custom thumbnail.\nTimeout: 60 sec",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.error(f"Error showing thumbnail setting: {e}")
    else:
        # Show instruction to set thumbnail
        keyboard = [
            [
                InlineKeyboardButton("Back", callback_data="back_to_settings"),
                InlineKeyboardButton("Close", callback_data="close_settings")
            ]
        ]
        
        try:
            await query.edit_message_caption(
                caption="Send a photo to save it as custom thumbnail.\nTimeout: 60 sec",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            try:
                await query.edit_message_text(
                    text="Send a photo to save it as custom thumbnail.\nTimeout: 60 sec",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.error(f"Error showing thumbnail setting: {e}")

async def refresh_settings_menu(query, user_id):
    """Refresh the settings menu with updated values."""
    settings = get_user_settings(user_id)
    
    settings_text = f"""
⚙️ **Settings for** `{query.from_user.first_name}` ⚙️

📤 Upload as {settings['upload_mode'].title()}
🖼️ Custom Thumbnail {'Exists' if settings['custom_thumbnail'] else 'Not Exists'}
📺 Resolution is {settings['resolution']}p
🎬 Vcodec is {settings['vcodec']}
🎨 Bits is {settings['bits']} Bits
📐 Aspect Ratio is {settings['aspect_ratio']}
🔧 CRF is {settings['crf']}
📋 Metadata is {'Enabled' if settings['metadata_enabled'] else 'Disabled'}
💧 Watermark is {'Set' if settings['watermark'] else 'None'}
📝 Auto Rename is {'Set' if settings['auto_rename'] else 'None'}
"""
    
    keyboard = [
        [InlineKeyboardButton(f"Upload Mode | {settings['upload_mode'].title()}", callback_data="toggle_upload_mode")],
        [
            InlineKeyboardButton("Resolution", callback_data="set_resolution"),
            InlineKeyboardButton("Vcodec", callback_data="set_vcodec")
        ],
        [
            InlineKeyboardButton("Bits", callback_data="set_bits"),
            InlineKeyboardButton("CRF", callback_data="set_crf")
        ],
        [
            InlineKeyboardButton("Set Metadata", callback_data="set_metadata"),
            InlineKeyboardButton("Set Watermark", callback_data="set_watermark")
        ],
        [
            InlineKeyboardButton("Thumbnail ✅" if settings['custom_thumbnail'] else "Set Thumbnail", callback_data="set_thumbnail"),
            InlineKeyboardButton("Aspect 16:9 ✅", callback_data="set_aspect_ratio")
        ],
        [InlineKeyboardButton("Set Auto Rename", callback_data="set_auto_rename")],
        [InlineKeyboardButton("❌ CLOSE", callback_data="close_settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Try to edit the caption first (if the message has a photo)
        await query.edit_message_caption(
            caption=settings_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except:
        # If that fails, try to edit the text (if it's a text message)
        try:
            await query.edit_message_text(
                text=settings_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            # If both fail, send a new message
            logger.error(f"Error refreshing settings menu: {e}")
            await query.message.reply_text(
                text=settings_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
